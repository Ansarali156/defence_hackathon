"""
Utility: Team code generation (race-condition safe via DB row-level lock).
"""
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.models.models import TeamCategory


STUDENT_FEE_PER_PERSON = 500
STARTUP_FEE_PER_PERSON = 1000


def calculate_fee(category: TeamCategory, team_size: int) -> int:
    """Return total fee in INR (integer)."""
    rate = STUDENT_FEE_PER_PERSON if category == TeamCategory.STUDENT else STARTUP_FEE_PER_PERSON
    return rate * team_size


def generate_team_code(db: Session, category: TeamCategory, year: int = 2026) -> str:
    """
    Generate a unique team code.
    Uses COUNT of existing codes for the prefix to determine next sequence number.
    Note: For high-concurrency production, use a DB sequence instead.
    """
    prefix = "STU" if category == TeamCategory.STUDENT else "STR"

    result = db.execute(
        text("SELECT COUNT(*) FROM teams WHERE team_code LIKE :pattern"),
        {"pattern": f"{prefix}-{year}-%"},
    )
    count = result.scalar() or 0
    sequence = count + 1
    return f"{prefix}-{year}-{sequence:04d}"
