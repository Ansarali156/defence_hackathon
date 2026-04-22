"""
Admin router — dashboard, teams, CSV exports, problem CRUD, deadlines, certificates.
"""
from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.config.database import get_db
from app.config.s3 import upload_file_to_s3
from app.middleware.auth import get_current_admin
from app.models.models import (
    Team, ProblemStatement, Submission, Payment,
    PaymentStatus, TeamCategory, EventConfig,
)
from app.schemas.schemas import (
    DashboardStatsOut,
    ProblemStatementOut,
    CreateProblemStatementRequest,
    UpdateProblemStatementRequest,
    UpdateDeadlinesRequest,
)
from app.services.csv_service import (
    export_teams_csv,
    export_payments_csv,
    export_submissions_csv,
)
from app.services.pdf_service import generate_certificate
from app.services.email_service import send_certificate_ready_email

router = APIRouter(prefix="/api/admin", tags=["Admin"])


# ---------------------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------------------

@router.get("/dashboard", response_model=DashboardStatsOut)
def dashboard(
    db: Session = Depends(get_db),
    _: dict = Depends(get_current_admin),
):
    total = db.query(func.count(Team.id)).scalar() or 0
    students = db.query(func.count(Team.id)).filter(Team.category == TeamCategory.STUDENT).scalar() or 0
    startups = db.query(func.count(Team.id)).filter(Team.category == TeamCategory.STARTUP).scalar() or 0
    paid = db.query(func.count(Team.id)).filter(Team.payment_status == PaymentStatus.SUCCESS).scalar() or 0
    pending_pay = total - paid
    total_rev = db.query(func.sum(Team.payment_amount)).filter(
        Team.payment_status == PaymentStatus.SUCCESS
    ).scalar() or 0
    total_sub = db.query(func.count(Submission.id)).scalar() or 0
    pending_sub = db.query(func.count(Team.id)).filter(
        Team.submission_status == "pending"
    ).scalar() or 0

    return DashboardStatsOut(
        total_teams=total,
        total_student_teams=students,
        total_startup_teams=startups,
        total_revenue=total_rev,
        paid_teams=paid,
        pending_payment_teams=pending_pay,
        total_submissions=total_sub,
        pending_submissions=pending_sub,
    )


# ---------------------------------------------------------------------------
# Teams
# ---------------------------------------------------------------------------

@router.get("/teams")
def list_teams(
    page: int = 1,
    page_size: int = 20,
    category: str = None,
    payment_status: str = None,
    submission_status: str = None,
    db: Session = Depends(get_db),
    _: dict = Depends(get_current_admin),
):
    q = db.query(Team)
    if category:
        q = q.filter(Team.category == category)
    if payment_status:
        q = q.filter(Team.payment_status == payment_status)
    if submission_status:
        q = q.filter(Team.submission_status == submission_status)
    total = q.count()
    teams = q.offset((page - 1) * page_size).limit(page_size).all()

    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "teams": [
            {
                "id": str(t.id),
                "team_code": t.team_code,
                "team_name": t.team_name,
                "category": t.category.value,
                "team_size": t.team_size,
                "lead_name": t.lead_name,
                "lead_email": t.lead_email,
                "lead_mobile": t.lead_mobile,
                "payment_status": t.payment_status.value,
                "payment_amount": float(t.payment_amount),
                "submission_status": t.submission_status.value,
                "selected_problem": t.selected_problem.title if t.selected_problem else None,
                "created_at": t.created_at.isoformat(),
            }
            for t in teams
        ],
    }


@router.get("/teams/{team_id}")
def get_team(
    team_id: UUID,
    db: Session = Depends(get_db),
    _: dict = Depends(get_current_admin),
):
    team = db.query(Team).filter(Team.id == team_id).first()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    return {
        "id": str(team.id),
        "team_code": team.team_code,
        "team_name": team.team_name,
        "category": team.category.value,
        "team_size": team.team_size,
        "lead_name": team.lead_name,
        "lead_email": team.lead_email,
        "lead_mobile": team.lead_mobile,
        "payment_status": team.payment_status.value,
        "payment_amount": float(team.payment_amount),
        "submission_status": team.submission_status.value,
        "selected_problem": (
            {
                "id": str(team.selected_problem.id),
                "code": team.selected_problem.problem_code,
                "title": team.selected_problem.title,
            }
            if team.selected_problem
            else None
        ),
        "members": [
            {"name": m.name, "email": m.email, "mobile": m.mobile}
            for m in team.members
        ],
        "submission": (
            {
                "abstract": team.submission.abstract,
                "description": team.submission.description,
                "project_file_url": team.submission.project_file_url,
                "presentation_url": team.submission.presentation_url,
                "deployment_link": team.submission.deployment_link,
                "certificate_approved": team.submission.certificate_approved,
                "certificate_url": team.submission.certificate_url,
                "submitted_at": team.submission.submitted_at.isoformat(),
            }
            if team.submission
            else None
        ),
        "created_at": team.created_at.isoformat(),
    }


# ---------------------------------------------------------------------------
# CSV Exports
# ---------------------------------------------------------------------------

@router.get("/export/teams.csv")
def export_teams(
    db: Session = Depends(get_db),
    _: dict = Depends(get_current_admin),
):
    csv_data = export_teams_csv(db)
    return Response(
        content=csv_data,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=teams.csv"},
    )


@router.get("/export/payments.csv")
def export_payments(
    db: Session = Depends(get_db),
    _: dict = Depends(get_current_admin),
):
    csv_data = export_payments_csv(db)
    return Response(
        content=csv_data,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=payments.csv"},
    )


@router.get("/export/submissions.csv")
def export_submissions(
    db: Session = Depends(get_db),
    _: dict = Depends(get_current_admin),
):
    csv_data = export_submissions_csv(db)
    return Response(
        content=csv_data,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=submissions.csv"},
    )


# ---------------------------------------------------------------------------
# Problem Statements
# ---------------------------------------------------------------------------

@router.post("/problem-statements", response_model=ProblemStatementOut, status_code=201)
def create_problem(
    body: CreateProblemStatementRequest,
    db: Session = Depends(get_db),
    _: dict = Depends(get_current_admin),
):
    existing = db.query(ProblemStatement).filter(
        ProblemStatement.problem_code == body.problem_code
    ).first()
    if existing:
        raise HTTPException(status_code=409, detail="Problem code already exists")

    ps = ProblemStatement(
        problem_code=body.problem_code,
        title=body.title,
        description=body.description,
        track=body.track,
    )
    db.add(ps)
    db.commit()
    db.refresh(ps)
    return ProblemStatementOut(
        id=ps.id, problem_code=ps.problem_code, title=ps.title,
        description=ps.description, track=ps.track, is_active=ps.is_active,
    )


@router.put("/problem-statements/{ps_id}", response_model=ProblemStatementOut)
def update_problem(
    ps_id: UUID,
    body: UpdateProblemStatementRequest,
    db: Session = Depends(get_db),
    _: dict = Depends(get_current_admin),
):
    ps = db.query(ProblemStatement).filter(ProblemStatement.id == ps_id).first()
    if not ps:
        raise HTTPException(status_code=404, detail="Problem statement not found")

    if body.title is not None:
        ps.title = body.title
    if body.description is not None:
        ps.description = body.description
    if body.track is not None:
        ps.track = body.track
    if body.is_active is not None:
        ps.is_active = body.is_active

    db.commit()
    db.refresh(ps)
    return ProblemStatementOut(
        id=ps.id, problem_code=ps.problem_code, title=ps.title,
        description=ps.description, track=ps.track, is_active=ps.is_active,
    )


@router.delete("/problem-statements/{ps_id}", status_code=204)
def delete_problem(
    ps_id: UUID,
    db: Session = Depends(get_db),
    _: dict = Depends(get_current_admin),
):
    ps = db.query(ProblemStatement).filter(ProblemStatement.id == ps_id).first()
    if not ps:
        raise HTTPException(status_code=404, detail="Problem statement not found")
    # Soft delete
    ps.is_active = False
    db.commit()


# ---------------------------------------------------------------------------
# Deadlines
# ---------------------------------------------------------------------------

@router.put("/config/deadlines")
def update_deadlines(
    body: UpdateDeadlinesRequest,
    db: Session = Depends(get_db),
    _: dict = Depends(get_current_admin),
):
    updates = {}
    if body.registration_deadline:
        updates["registration_deadline"] = body.registration_deadline.isoformat()
    if body.submission_deadline:
        updates["submission_deadline"] = body.submission_deadline.isoformat()

    for key, value in updates.items():
        row = db.query(EventConfig).filter(EventConfig.key == key).first()
        if row:
            row.value = value
        else:
            db.add(EventConfig(key=key, value=value))

    db.commit()
    return {"message": "Deadlines updated", "updated": list(updates.keys())}


# ---------------------------------------------------------------------------
# Certificate Approval
# ---------------------------------------------------------------------------

@router.post("/certificates/approve/{team_id}")
async def approve_certificate(
    team_id: UUID,
    db: Session = Depends(get_db),
    _: dict = Depends(get_current_admin),
):
    team = db.query(Team).filter(Team.id == team_id).first()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    if not team.submission:
        raise HTTPException(status_code=404, detail="Team has no submission")

    sub = team.submission

    # Generate PDF certificate
    pdf_bytes = generate_certificate(
        team_name=team.team_name,
        team_code=team.team_code,
        problem_title=sub.problem_statement.title if sub.problem_statement else "N/A",
        submitted_at=sub.submitted_at,
    )

    key = f"certificates/{team.team_code}/certificate.pdf"
    cert_url = upload_file_to_s3(pdf_bytes, key, "application/pdf")

    sub.certificate_approved = True
    sub.certificate_url = cert_url
    db.commit()

    await send_certificate_ready_email(
        to_email=team.lead_email,
        team_name=team.team_name,
        certificate_url=cert_url,
    )

    return {"message": "Certificate approved and sent to team", "certificate_url": cert_url}


# ---------------------------------------------------------------------------
# Invoice Download
# ---------------------------------------------------------------------------

@router.get("/payments/{team_id}/invoice")
def get_invoice(
    team_id: UUID,
    db: Session = Depends(get_db),
    _: dict = Depends(get_current_admin),
):
    payment = (
        db.query(Payment)
        .filter(Payment.team_id == team_id)
        .order_by(Payment.created_at.desc())
        .first()
    )
    if not payment or not payment.invoice_url:
        raise HTTPException(status_code=404, detail="Invoice not found")
    from fastapi.responses import RedirectResponse
    from app.config.s3 import generate_presigned_url
    key = payment.invoice_url.split(".amazonaws.com/")[-1]
    return RedirectResponse(url=generate_presigned_url(key))
