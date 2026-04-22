"""
E2E tests for registration and payment flow using TestClient.
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.config.database import Base, get_db

# Use in-memory SQLite for tests
SQLALCHEMY_TEST_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_TEST_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db

Base.metadata.create_all(bind=engine)

client = TestClient(app)


@pytest.fixture(autouse=True)
def clean_db():
    """Drop and recreate tables before each test."""
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield


def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_register_student_team():
    response = client.post("/api/register/student", json={
        "team_name": "Alpha Squad",
        "team_size": 2,
        "lead_name": "Alice",
        "lead_email": "alice@example.com",
        "lead_mobile": "9876543210",
        "password": "Alice@2026",
        "confirm_password": "Alice@2026",
        "members": [
            {"name": "Bob", "email": "bob@example.com", "mobile": "9876543211"}
        ],
    })
    assert response.status_code == 201
    data = response.json()
    assert data["team_code"].startswith("STU-2026-")
    assert float(data["payment_amount"]) == 1000.0


def test_register_duplicate_email():
    payload = {
        "team_name": "Alpha Squad",
        "team_size": 2,
        "lead_name": "Alice",
        "lead_email": "alice@example.com",
        "lead_mobile": "9876543210",
        "password": "Alice@2026",
        "confirm_password": "Alice@2026",
        "members": [
            {"name": "Bob", "email": "bob@example.com", "mobile": "9876543211"}
        ],
    }
    client.post("/api/register/student", json=payload)
    response = client.post("/api/register/student", json=payload)
    assert response.status_code == 409


def test_invalid_team_size():
    response = client.post("/api/register/student", json={
        "team_name": "Solo",
        "team_size": 1,
        "lead_name": "Alice",
        "lead_email": "alice2@example.com",
        "lead_mobile": "9876543210",
        "password": "Alice@2026",
        "confirm_password": "Alice@2026",
        "members": [],
    })
    assert response.status_code == 422


def test_login_after_register():
    client.post("/api/register/student", json={
        "team_name": "Beta Team",
        "team_size": 2,
        "lead_name": "Carol",
        "lead_email": "carol@example.com",
        "lead_mobile": "9876543210",
        "password": "Carol@2026",
        "confirm_password": "Carol@2026",
        "members": [
            {"name": "Dave", "email": "dave@example.com", "mobile": "9876543211"}
        ],
    })
    response = client.post("/api/auth/login", json={
        "email": "carol@example.com",
        "password": "Carol@2026",
    })
    assert response.status_code == 200
    assert "access_token" in response.json()
