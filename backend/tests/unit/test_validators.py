"""
Unit tests for team ID generation and fee calculation.
"""
import pytest
from unittest.mock import MagicMock
from sqlalchemy.orm import Session

from app.models.models import TeamCategory
from app.utils.team_id_generator import calculate_fee, generate_team_code
from app.utils.validators import validate_password, validate_file


# ---------------------------------------------------------------------------
# Fee Calculation
# ---------------------------------------------------------------------------

def test_student_fee():
    assert calculate_fee(TeamCategory.STUDENT, 2) == 1000
    assert calculate_fee(TeamCategory.STUDENT, 5) == 2500


def test_startup_fee():
    assert calculate_fee(TeamCategory.STARTUP, 2) == 2000
    assert calculate_fee(TeamCategory.STARTUP, 3) == 3000


# ---------------------------------------------------------------------------
# Password Validation
# ---------------------------------------------------------------------------

def test_password_too_short():
    assert validate_password("Ab@12") is False


def test_password_missing_uppercase():
    assert validate_password("abcdef@1") is False


def test_password_missing_lowercase():
    assert validate_password("ABCDEF@1") is False


def test_password_missing_special():
    assert validate_password("Abcdef123") is False


def test_password_valid():
    assert validate_password("SecureP@ss1") is True


# ---------------------------------------------------------------------------
# File Validation
# ---------------------------------------------------------------------------

def test_file_too_large():
    ok, msg = validate_file("application/pdf", 11 * 1024 * 1024)
    assert ok is False
    assert "10MB" in msg


def test_invalid_mime():
    ok, msg = validate_file("image/png", 1024)
    assert ok is False
    assert "not allowed" in msg


def test_valid_pdf():
    ok, msg = validate_file("application/pdf", 1024 * 1024)
    assert ok is True
