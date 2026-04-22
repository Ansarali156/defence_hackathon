"""
Payment router — Razorpay order creation, verification, and webhook.
"""
import json
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.config.database import get_db
from app.config.settings import settings
from app.middleware.auth import get_current_team
from app.models.models import Team, Payment, PaymentStatus, PaymentOrderStatus
from app.schemas.schemas import (
    CreatePaymentOrderRequest,
    CreatePaymentOrderResponse,
    VerifyPaymentRequest,
    VerifyPaymentResponse,
)
from app.services.payment_service import (
    create_razorpay_order,
    verify_payment_signature,
    verify_webhook_signature,
)
from app.services.email_service import send_payment_confirmation
from app.services.pdf_service import generate_payment_invoice
from app.config.s3 import upload_file_to_s3

router = APIRouter(prefix="/api/payment", tags=["Payment"])


@router.post("/create-order", response_model=CreatePaymentOrderResponse)
def create_order(
    body: CreatePaymentOrderRequest,
    db: Session = Depends(get_db),
):
    team = db.query(Team).filter(Team.id == body.team_id).first()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    if team.payment_status == PaymentStatus.SUCCESS:
        raise HTTPException(status_code=409, detail="Payment already completed")

    order = create_razorpay_order(int(team.payment_amount), team.team_code)

    payment = Payment(
        team_id=team.id,
        razorpay_order_id=order["id"],
        amount=team.payment_amount,
        currency="INR",
        status=PaymentOrderStatus.CREATED,
    )
    db.add(payment)
    db.commit()

    return CreatePaymentOrderResponse(
        order_id=order["id"],
        amount=int(team.payment_amount) * 100,
        currency="INR",
        key_id=settings.RAZORPAY_KEY_ID,
    )


@router.post("/verify", response_model=VerifyPaymentResponse)
async def verify_payment(
    body: VerifyPaymentRequest,
    db: Session = Depends(get_db),
):
    team = db.query(Team).filter(Team.id == body.team_id).first()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")

    is_valid = verify_payment_signature(
        body.razorpay_order_id,
        body.razorpay_payment_id,
        body.razorpay_signature,
    )
    if not is_valid:
        raise HTTPException(status_code=400, detail="Payment verification failed — invalid signature")

    # Update payment record
    payment = (
        db.query(Payment)
        .filter(Payment.razorpay_order_id == body.razorpay_order_id)
        .first()
    )
    if payment:
        payment.razorpay_payment_id = body.razorpay_payment_id
        payment.razorpay_signature = body.razorpay_signature
        payment.status = PaymentOrderStatus.PAID

        # Generate invoice PDF and upload to S3
        try:
            pdf_bytes = generate_payment_invoice(
                team_name=team.team_name,
                team_code=team.team_code,
                amount=int(team.payment_amount),
                payment_id=body.razorpay_payment_id,
                paid_at=datetime.now(timezone.utc),
            )
            key = f"invoices/{team.team_code}/invoice.pdf"
            invoice_url = upload_file_to_s3(pdf_bytes, key, "application/pdf")
            payment.invoice_url = invoice_url
        except Exception:
            pass  # don't fail payment confirmation if invoice upload fails

    team.payment_status = PaymentStatus.SUCCESS
    db.commit()

    await send_payment_confirmation(
        to_email=team.lead_email,
        team_name=team.team_name,
        team_code=team.team_code,
        amount=int(team.payment_amount),
    )

    return VerifyPaymentResponse(success=True, message="Payment verified successfully")


@router.post("/webhook")
async def razorpay_webhook(request: Request, db: Session = Depends(get_db)):
    """Idempotent fallback webhook handler from Razorpay."""
    signature = request.headers.get("X-Razorpay-Signature", "")
    body = await request.body()

    if not verify_webhook_signature(body, signature):
        raise HTTPException(status_code=400, detail="Invalid webhook signature")

    payload = json.loads(body)
    event = payload.get("event")

    if event == "payment.captured":
        payment_entity = payload["payload"]["payment"]["entity"]
        order_id = payment_entity.get("order_id")
        payment_id = payment_entity.get("id")

        payment = db.query(Payment).filter(Payment.razorpay_order_id == order_id).first()
        if payment and payment.status != PaymentOrderStatus.PAID:
            payment.razorpay_payment_id = payment_id
            payment.status = PaymentOrderStatus.PAID
            if payment.team:
                payment.team.payment_status = PaymentStatus.SUCCESS
            db.commit()

    return {"status": "ok"}
