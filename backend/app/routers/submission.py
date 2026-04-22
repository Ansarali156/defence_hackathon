"""
Submission router — file upload, submit, status, certificate download.
"""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.config.database import get_db
from app.config.s3 import upload_file_to_s3, generate_presigned_url
from app.middleware.auth import get_current_team
from app.middleware.deadline import check_submission_open
from app.models.models import Team, Submission, PaymentStatus, SubmissionStatus
from app.schemas.schemas import SubmitRequest, SubmissionStatusOut
from app.utils.validators import validate_file

router = APIRouter(prefix="/api/submission", tags=["Submission"])


def _get_paid_team(db: Session, payload: dict) -> Team:
    team = db.query(Team).filter(Team.id == payload["sub"]).first()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    if team.payment_status != PaymentStatus.SUCCESS:
        raise HTTPException(status_code=403, detail="Payment required")
    if not team.selected_problem_id:
        raise HTTPException(status_code=403, detail="Problem statement must be selected before submitting")
    return team


@router.post("/upload")
async def upload_files(
    project_file: UploadFile = File(None),
    presentation: UploadFile = File(None),
    db: Session = Depends(get_db),
    payload: dict = Depends(get_current_team),
    _: None = Depends(check_submission_open),
):
    team = _get_paid_team(db, payload)

    sub = db.query(Submission).filter(Submission.team_id == team.id).first()
    if not sub:
        sub = Submission(
            team_id=team.id,
            problem_statement_id=team.selected_problem_id,
            abstract="",
            description="",
        )
        db.add(sub)
        db.flush()

    urls = {}
    for upload, field_name in [(project_file, "project_file"), (presentation, "presentation")]:
        if upload is None:
            continue
        content = await upload.read()
        ok, err = validate_file(upload.content_type, len(content))
        if not ok:
            raise HTTPException(status_code=413 if "size" in err else 415, detail=err)

        key = f"submissions/{team.team_code}/{field_name}_{upload.filename}"
        url = upload_file_to_s3(content, key, upload.content_type)
        urls[field_name] = url

    if "project_file" in urls:
        sub.project_file_url = urls["project_file"]
    if "presentation" in urls:
        sub.presentation_url = urls["presentation"]

    db.commit()
    return {"message": "Files uploaded successfully", "urls": urls}


@router.post("/submit")
def submit(
    body: SubmitRequest,
    db: Session = Depends(get_db),
    payload: dict = Depends(get_current_team),
    _: None = Depends(check_submission_open),
):
    team = _get_paid_team(db, payload)

    sub = db.query(Submission).filter(Submission.team_id == team.id).first()
    if not sub:
        sub = Submission(
            team_id=team.id,
            problem_statement_id=team.selected_problem_id,
        )
        db.add(sub)

    sub.abstract = body.abstract
    sub.description = body.description
    sub.deployment_link = body.deployment_link
    team.submission_status = SubmissionStatus.SUBMITTED

    db.commit()
    return {"message": "Submission recorded successfully"}


@router.get("/status", response_model=SubmissionStatusOut)
def submission_status(
    db: Session = Depends(get_db),
    payload: dict = Depends(get_current_team),
):
    team = db.query(Team).filter(Team.id == payload["sub"]).first()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")

    sub = team.submission
    if not sub:
        return SubmissionStatusOut(
            status=SubmissionStatus.PENDING,
            abstract=None, description=None,
            project_file_url=None, presentation_url=None,
            deployment_link=None, submitted_at=None,
            certificate_approved=False, certificate_url=None,
        )
    return SubmissionStatusOut(
        status=team.submission_status,
        abstract=sub.abstract,
        description=sub.description,
        project_file_url=sub.project_file_url,
        presentation_url=sub.presentation_url,
        deployment_link=sub.deployment_link,
        submitted_at=sub.submitted_at,
        certificate_approved=sub.certificate_approved,
        certificate_url=sub.certificate_url,
    )


@router.get("/certificate")
def download_certificate(
    db: Session = Depends(get_db),
    payload: dict = Depends(get_current_team),
):
    team = db.query(Team).filter(Team.id == payload["sub"]).first()
    if not team or not team.submission:
        raise HTTPException(status_code=404, detail="No submission found")
    if not team.submission.certificate_approved:
        raise HTTPException(status_code=403, detail="Certificate not yet approved by admin")
    if not team.submission.certificate_url:
        raise HTTPException(status_code=404, detail="Certificate URL not available yet")

    # Generate presigned URL for secure download
    key = team.submission.certificate_url.split(".amazonaws.com/")[-1]
    presigned = generate_presigned_url(key, expiry=300)
    return RedirectResponse(url=presigned)
