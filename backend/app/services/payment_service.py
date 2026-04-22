"""
Razorpay payment service — order creation and HMAC signature verification.
"""
import hashlib
import hmac

from app.config.razorpay import razorpay_client
from app.config.settings import settings


def create_razorpay_order(amount_inr: int, team_code: str) -> dict:
    """
    Create a Razorpay order.
    amount_inr: total amount in INR (converted to paise internally).
    Returns the raw Razorpay order dict.
    """
    order_data = {
        "amount": amount_inr * 100,  # paise
        "currency": "INR",
        "receipt": team_code,
        "payment_capture": 1,  # auto-capture
    }
    return razorpay_client.order.create(data=order_data)


def verify_payment_signature(
    order_id: str,
    payment_id: str,
    signature: str,
) -> bool:
    """
    Verify Razorpay HMAC-SHA256 signature.
    Returns True if valid, False otherwise.
    """
    body = f"{order_id}|{payment_id}"
    expected = hmac.new(
        settings.RAZORPAY_KEY_SECRET.encode("utf-8"),
        body.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()
    return hmac.compare_digest(expected, signature)


def verify_webhook_signature(payload_body: bytes, signature: str) -> bool:
    """Verify Razorpay webhook HMAC-SHA256 signature."""
    expected = hmac.new(
        settings.RAZORPAY_WEBHOOK_SECRET.encode("utf-8"),
        payload_body,
        hashlib.sha256,
    ).hexdigest()
    return hmac.compare_digest(expected, signature)
