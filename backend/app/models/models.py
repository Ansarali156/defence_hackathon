import uuid
import enum
from decimal import Decimal
from datetime import datetime, timezone

from sqlalchemy import (
    Column, String, Integer, Enum, Boolean, Numeric,
    DateTime, ForeignKey, Text, UniqueConstraint, func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.config.database import Base


def utcnow():
    return datetime.now(timezone.utc)


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class TeamCategory(str, enum.Enum):
    STUDENT = "student"
    STARTUP = "startup"


class PaymentStatus(str, enum.Enum):
    PENDING = "pending"
    SUCCESS = "success"
    FAILED = "failed"


class PaymentOrderStatus(str, enum.Enum):
    CREATED = "created"
    PAID = "paid"
    FAILED = "failed"


class SubmissionStatus(str, enum.Enum):
    PENDING = "pending"
    SUBMITTED = "submitted"


# ---------------------------------------------------------------------------
# Teams
# ---------------------------------------------------------------------------

class Team(Base):
    __tablename__ = "teams"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    team_code = Column(String(20), unique=True, nullable=False, index=True)
    team_name = Column(String(100), nullable=False)
    category = Column(Enum(TeamCategory), nullable=False)
    team_size = Column(Integer, nullable=False)

    # Lead details
    lead_name = Column(String(100), nullable=False)
    lead_email = Column(String(150), unique=True, nullable=False, index=True)
    lead_mobile = Column(String(15), nullable=False)
    password_hash = Column(String(255), nullable=False)

    # Payment
    payment_status = Column(Enum(PaymentStatus), default=PaymentStatus.PENDING, nullable=False)
    payment_amount = Column(Numeric(10, 2), nullable=False)

    # Problem / Submission
    selected_problem_id = Column(UUID(as_uuid=True), ForeignKey("problem_statements.id"), nullable=True)
    submission_status = Column(Enum(SubmissionStatus), default=SubmissionStatus.PENDING, nullable=False)

    # Password reset
    reset_token = Column(String(255), nullable=True)
    reset_token_expiry = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)

    # Relationships
    members = relationship("TeamMember", back_populates="team", cascade="all, delete-orphan")
    selected_problem = relationship("ProblemStatement", back_populates="teams")
    submission = relationship("Submission", back_populates="team", uselist=False)
    payments = relationship("Payment", back_populates="team")


class TeamMember(Base):
    __tablename__ = "team_members"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    team_id = Column(UUID(as_uuid=True), ForeignKey("teams.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(100), nullable=False)
    email = Column(String(150), nullable=False)
    mobile = Column(String(15), nullable=False)

    team = relationship("Team", back_populates="members")


# ---------------------------------------------------------------------------
# Problem Statements
# ---------------------------------------------------------------------------

class ProblemStatement(Base):
    __tablename__ = "problem_statements"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    problem_code = Column(String(20), unique=True, nullable=False)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=False)
    track = Column(String(100), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)

    teams = relationship("Team", back_populates="selected_problem")
    submissions = relationship("Submission", back_populates="problem_statement")


# ---------------------------------------------------------------------------
# Submissions
# ---------------------------------------------------------------------------

class Submission(Base):
    __tablename__ = "submissions"
    __table_args__ = (UniqueConstraint("team_id", name="uq_submission_team"),)

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    team_id = Column(UUID(as_uuid=True), ForeignKey("teams.id", ondelete="CASCADE"), nullable=False)
    problem_statement_id = Column(UUID(as_uuid=True), ForeignKey("problem_statements.id"), nullable=False)

    abstract = Column(Text, nullable=False)
    description = Column(Text, nullable=False)
    project_file_url = Column(String(500), nullable=True)
    presentation_url = Column(String(500), nullable=True)
    deployment_link = Column(String(500), nullable=True)

    certificate_approved = Column(Boolean, default=False, nullable=False)
    certificate_url = Column(String(500), nullable=True)

    submitted_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)

    team = relationship("Team", back_populates="submission")
    problem_statement = relationship("ProblemStatement", back_populates="submissions")


# ---------------------------------------------------------------------------
# Payments
# ---------------------------------------------------------------------------

class Payment(Base):
    __tablename__ = "payments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    team_id = Column(UUID(as_uuid=True), ForeignKey("teams.id", ondelete="CASCADE"), nullable=False)

    razorpay_order_id = Column(String(100), nullable=True, index=True)
    razorpay_payment_id = Column(String(100), nullable=True)
    razorpay_signature = Column(String(255), nullable=True)

    amount = Column(Numeric(10, 2), nullable=False)
    currency = Column(String(10), default="INR", nullable=False)
    status = Column(Enum(PaymentOrderStatus), default=PaymentOrderStatus.CREATED, nullable=False)
    invoice_url = Column(String(500), nullable=True)

    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)

    team = relationship("Team", back_populates="payments")


# ---------------------------------------------------------------------------
# Admins
# ---------------------------------------------------------------------------

class Admin(Base):
    __tablename__ = "admins"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(150), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    name = Column(String(100), nullable=False)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)


# ---------------------------------------------------------------------------
# Event Config (key-value store for deadlines etc.)
# ---------------------------------------------------------------------------

class EventConfig(Base):
    __tablename__ = "event_config"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    key = Column(String(50), unique=True, nullable=False)
    value = Column(String(255), nullable=False)
