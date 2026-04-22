"""
Public event router — event status, details.
"""
from datetime import datetime, timezone
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.config.database import get_db
from app.models.models import EventConfig
from app.schemas.schemas import EventStatusOut

router = APIRouter(prefix="/api/event", tags=["Event"])


def _get_config(db: Session, key: str) -> datetime | None:
    row = db.query(EventConfig).filter(EventConfig.key == key).first()
    if row is None:
        return None
    try:
        return datetime.fromisoformat(row.value)
    except ValueError:
        return None


@router.get("/status", response_model=EventStatusOut)
def event_status(db: Session = Depends(get_db)):
    now = datetime.now(timezone.utc)
    reg_dl = _get_config(db, "registration_deadline")
    sub_dl = _get_config(db, "submission_deadline")
    return EventStatusOut(
        registration_open=reg_dl is None or now < reg_dl,
        submission_open=sub_dl is None or now < sub_dl,
        registration_deadline=reg_dl,
        submission_deadline=sub_dl,
    )


@router.get("/details")
def event_details():
    return {
        "name": "Defense Hackathon 2026",
        "description": "A national-level hackathon focused on defense and security innovations.",
        "year": 2026,
        "contact_email": "info@defensehackathon2026.com",
    }
