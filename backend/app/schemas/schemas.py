"""
Pydantic v2 schemas for request / response validation.
"""
import re
from datetime import datetime
from decimal import Decimal
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr, field_validator, model_validator

from app.models.models import TeamCategory, PaymentStatus, SubmissionStatus, PaymentOrderStatus


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

def validate_password_strength(v: str) -> str:
    if len(v) < 6:
        raise ValueError("Password must be at least 6 characters")
    if not re.search(r"[A-Z]", v):
        raise ValueError("Password must contain at least one uppercase letter")
    if not re.search(r"[a-z]", v):
        raise ValueError("Password must contain at least one lowercase letter")
    if not re.search(r"[^a-zA-Z0-9]", v):
        raise ValueError("Password must contain at least one special character")
    return v


# ---------------------------------------------------------------------------
# Team Member
# ---------------------------------------------------------------------------

class TeamMemberCreate(BaseModel):
    name: str
    email: EmailStr
    mobile: str


class TeamMemberOut(BaseModel):
    id: UUID
    name: str
    email: EmailStr
    mobile: str

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Registration
# ---------------------------------------------------------------------------

class RegisterStudentTeamRequest(BaseModel):
    team_name: str
    team_size: int
    lead_name: str
    lead_email: EmailStr
    lead_mobile: str
    password: str
    confirm_password: str
    members: List[TeamMemberCreate]

    @field_validator("team_size")
    @classmethod
    def validate_team_size(cls, v: int) -> int:
        if not (2 <= v <= 5):
            raise ValueError("Student team size must be between 2 and 5")
        return v

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        return validate_password_strength(v)

    @model_validator(mode="after")
    def passwords_match(self) -> "RegisterStudentTeamRequest":
        if self.password != self.confirm_password:
            raise ValueError("Passwords do not match")
        if len(self.members) != self.team_size - 1:
            raise ValueError(f"Expected {self.team_size - 1} additional members for team_size={self.team_size}")
        return self


class RegisterStartupTeamRequest(BaseModel):
    team_name: str
    team_size: int
    lead_name: str
    lead_email: EmailStr
    lead_mobile: str
    password: str
    confirm_password: str
    members: List[TeamMemberCreate]

    @field_validator("team_size")
    @classmethod
    def validate_team_size(cls, v: int) -> int:
        if not (2 <= v <= 3):
            raise ValueError("Startup team size must be between 2 and 3")
        return v

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        return validate_password_strength(v)

    @model_validator(mode="after")
    def passwords_match(self) -> "RegisterStartupTeamRequest":
        if self.password != self.confirm_password:
            raise ValueError("Passwords do not match")
        if len(self.members) != self.team_size - 1:
            raise ValueError(f"Expected {self.team_size - 1} additional members for team_size={self.team_size}")
        return self


class RegisterTeamResponse(BaseModel):
    team_code: str
    team_id: UUID
    payment_amount: Decimal
    message: str

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------

class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str
    confirm_password: str

    @field_validator("new_password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        return validate_password_strength(v)

    @model_validator(mode="after")
    def passwords_match(self) -> "ResetPasswordRequest":
        if self.new_password != self.confirm_password:
            raise ValueError("Passwords do not match")
        return self


# ---------------------------------------------------------------------------
# Payment
# ---------------------------------------------------------------------------

class CreatePaymentOrderRequest(BaseModel):
    team_id: UUID


class CreatePaymentOrderResponse(BaseModel):
    order_id: str
    amount: int  # in paise
    currency: str
    key_id: str


class VerifyPaymentRequest(BaseModel):
    team_id: UUID
    razorpay_order_id: str
    razorpay_payment_id: str
    razorpay_signature: str


class VerifyPaymentResponse(BaseModel):
    success: bool
    message: str


# ---------------------------------------------------------------------------
# Team / Problem
# ---------------------------------------------------------------------------

class ProblemStatementOut(BaseModel):
    id: UUID
    problem_code: str
    title: str
    description: str
    track: str
    is_active: bool
    teams_selected: int = 0

    model_config = {"from_attributes": True}


class TeamProfileOut(BaseModel):
    id: UUID
    team_code: str
    team_name: str
    category: TeamCategory
    team_size: int
    lead_name: str
    lead_email: EmailStr
    lead_mobile: str
    payment_status: PaymentStatus
    payment_amount: Decimal
    submission_status: SubmissionStatus
    selected_problem: Optional[ProblemStatementOut]
    members: List[TeamMemberOut]
    created_at: datetime

    model_config = {"from_attributes": True}


class SelectProblemRequest(BaseModel):
    problem_id: UUID


# ---------------------------------------------------------------------------
# Submission
# ---------------------------------------------------------------------------

class SubmitRequest(BaseModel):
    abstract: str
    description: str
    deployment_link: Optional[str] = None


class SubmissionStatusOut(BaseModel):
    status: SubmissionStatus
    abstract: Optional[str]
    description: Optional[str]
    project_file_url: Optional[str]
    presentation_url: Optional[str]
    deployment_link: Optional[str]
    submitted_at: Optional[datetime]
    certificate_approved: bool
    certificate_url: Optional[str]

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Admin — Dashboard
# ---------------------------------------------------------------------------

class DashboardStatsOut(BaseModel):
    total_teams: int
    total_student_teams: int
    total_startup_teams: int
    total_revenue: Decimal
    paid_teams: int
    pending_payment_teams: int
    total_submissions: int
    pending_submissions: int


# ---------------------------------------------------------------------------
# Admin — Problem Statements
# ---------------------------------------------------------------------------

class CreateProblemStatementRequest(BaseModel):
    problem_code: str
    title: str
    description: str
    track: str


class UpdateProblemStatementRequest(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    track: Optional[str] = None
    is_active: Optional[bool] = None


# ---------------------------------------------------------------------------
# Admin — Deadlines
# ---------------------------------------------------------------------------

class UpdateDeadlinesRequest(BaseModel):
    registration_deadline: Optional[datetime] = None
    submission_deadline: Optional[datetime] = None


# ---------------------------------------------------------------------------
# Event / Public
# ---------------------------------------------------------------------------

class EventStatusOut(BaseModel):
    registration_open: bool
    submission_open: bool
    registration_deadline: Optional[datetime]
    submission_deadline: Optional[datetime]
