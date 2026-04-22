"""
Auth router — login (team + admin), forgot/reset password, logout.
"""
import secrets
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from app.config.database import get_db
from app.config.settings import settings
from app.middleware.auth import create_access_token, get_current_team
from app.models.models import Team, Admin
from app.schemas.schemas import (
    LoginRequest,
    TokenResponse,
    ForgotPasswordRequest,
    ResetPasswordRequest,
)
from app.services.email_service import (
    send_password_reset_email,
    send_password_set_confirmation,
)

router = APIRouter(prefix="/api/auth", tags=["Auth"])
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


@router.post("/login", response_model=TokenResponse)
def team_login(body: LoginRequest, db: Session = Depends(get_db)):
    team = db.query(Team).filter(Team.lead_email == body.email).first()
    if not team or not pwd_context.verify(body.password, team.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    token = create_access_token({
        "sub": str(team.id),
        "email": team.lead_email,
        "role": team.category.value,
        "team_code": team.team_code,
    })
    return TokenResponse(
        access_token=token,
        expires_in=settings.JWT_EXPIRY_HOURS * 3600,
    )


@router.post("/admin/login", response_model=TokenResponse)
def admin_login(body: LoginRequest, db: Session = Depends(get_db)):
    admin = db.query(Admin).filter(Admin.email == body.email).first()
    if not admin or not pwd_context.verify(body.password, admin.password_hash):
        raise HTTPException(status_code=401, detail="Invalid admin credentials")

    token = create_access_token({
        "sub": str(admin.id),
        "email": admin.email,
        "role": "admin",
    })
    return TokenResponse(
        access_token=token,
        expires_in=settings.JWT_EXPIRY_HOURS * 3600,
    )


@router.post("/forgot-password")
async def forgot_password(body: ForgotPasswordRequest, db: Session = Depends(get_db)):
    team = db.query(Team).filter(Team.lead_email == body.email).first()
    if not team:
        # Don't reveal whether email exists
        return {"message": "If that email is registered, a reset link has been sent."}

    token = secrets.token_urlsafe(32)
    team.reset_token = token
    team.reset_token_expiry = datetime.now(timezone.utc) + timedelta(hours=1)
    db.commit()

    reset_link = f"{settings.FRONTEND_URL}/reset-password?token={token}"
    await send_password_reset_email(team.lead_email, reset_link)

    return {"message": "If that email is registered, a reset link has been sent."}


@router.post("/reset-password")
async def reset_password(body: ResetPasswordRequest, db: Session = Depends(get_db)):
    team = db.query(Team).filter(Team.reset_token == body.token).first()
    if not team:
        raise HTTPException(status_code=400, detail="Invalid or expired reset token")
    if team.reset_token_expiry and datetime.now(timezone.utc) > team.reset_token_expiry:
        raise HTTPException(status_code=400, detail="Reset token has expired")

    team.password_hash = pwd_context.hash(body.new_password)
    team.reset_token = None
    team.reset_token_expiry = None
    db.commit()

    await send_password_set_confirmation(team.lead_email, team.team_name)
    return {"message": "Password reset successfully"}


@router.post("/logout")
def logout(payload: dict = Depends(get_current_team)):
    # JWT is stateless; client discards token. Future: add token blacklist if needed.
    return {"message": "Logged out successfully"}
