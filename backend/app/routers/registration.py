"""
Registration router — POST /api/register/student | /api/register/startup
"""
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from app.config.database import get_db
from app.middleware.deadline import check_registration_open
from app.models.models import Team, TeamMember, TeamCategory
from app.schemas.schemas import (
    RegisterStudentTeamRequest,
    RegisterStartupTeamRequest,
    RegisterTeamResponse,
)
from app.services.email_service import send_registration_confirmation
from app.utils.team_id_generator import generate_team_code, calculate_fee

router = APIRouter(prefix="/api/register", tags=["Registration"])
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def _create_team(db: Session, data, category: TeamCategory) -> Team:
    fee = calculate_fee(category, data.team_size)
    team_code = generate_team_code(db, category)

    team = Team(
        team_code=team_code,
        team_name=data.team_name,
        category=category,
        team_size=data.team_size,
        lead_name=data.lead_name,
        lead_email=data.lead_email,
        lead_mobile=data.lead_mobile,
        password_hash=pwd_context.hash(data.password),
        payment_amount=Decimal(fee),
    )
    db.add(team)
    db.flush()  # get team.id before adding members

    for m in data.members:
        db.add(TeamMember(
            team_id=team.id,
            name=m.name,
            email=m.email,
            mobile=m.mobile,
        ))

    db.commit()
    db.refresh(team)
    return team


@router.post("/student", response_model=RegisterTeamResponse, status_code=201)
async def register_student_team(
    body: RegisterStudentTeamRequest,
    db: Session = Depends(get_db),
    _: None = Depends(check_registration_open),
):
    existing = db.query(Team).filter(Team.lead_email == body.lead_email).first()
    if existing:
        raise HTTPException(status_code=409, detail="Email already registered")

    team = _create_team(db, body, TeamCategory.STUDENT)
    await send_registration_confirmation(
        to_email=team.lead_email,
        team_name=team.team_name,
        team_code=team.team_code,
        payment_amount=int(team.payment_amount),
    )
    return RegisterTeamResponse(
        team_code=team.team_code,
        team_id=team.id,
        payment_amount=team.payment_amount,
        message="Registration successful. Please complete payment to confirm your spot.",
    )


@router.post("/startup", response_model=RegisterTeamResponse, status_code=201)
async def register_startup_team(
    body: RegisterStartupTeamRequest,
    db: Session = Depends(get_db),
    _: None = Depends(check_registration_open),
):
    existing = db.query(Team).filter(Team.lead_email == body.lead_email).first()
    if existing:
        raise HTTPException(status_code=409, detail="Email already registered")

    team = _create_team(db, body, TeamCategory.STARTUP)
    await send_registration_confirmation(
        to_email=team.lead_email,
        team_name=team.team_name,
        team_code=team.team_code,
        payment_amount=int(team.payment_amount),
    )
    return RegisterTeamResponse(
        team_code=team.team_code,
        team_id=team.id,
        payment_amount=team.payment_amount,
        message="Registration successful. Please complete payment to confirm your spot.",
    )
