"""
Deadline enforcement dependency.
Reads registration_deadline / submission_deadline from event_config table.
"""
from datetime import datetime, timezone
from functools import lru_cache
from typing import Literal

from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session

from app.config.database import get_db
from app.models.models import EventConfig


def _get_deadline(db: Session, key: str) -> datetime | None:
    row = db.query(EventConfig).filter(EventConfig.key == key).first()
    if row is None:
        return None
    try:
        return datetime.fromisoformat(row.value)
    except ValueError:
        return None


def check_registration_open(db: Session = Depends(get_db)):
    deadline = _get_deadline(db, "registration_deadline")
    if deadline and datetime.now(timezone.utc) > deadline:
        raise HTTPException(
            status_code=403,
            detail="Registration is closed. The deadline has passed.",
        )


def check_submission_open(db: Session = Depends(get_db)):
    deadline = _get_deadline(db, "submission_deadline")
    if deadline and datetime.now(timezone.utc) > deadline:
        raise HTTPException(
            status_code=403,
            detail="Submission is closed. The deadline has passed.",
        )
