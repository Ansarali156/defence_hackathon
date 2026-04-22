"""
Script to seed the database with:
- One admin account
- Sample problem statements
- Default event deadlines

Run once after migrations:
    python seed.py
"""
import sys
from datetime import datetime, timezone, timedelta

from passlib.context import CryptContext
from sqlalchemy.orm import Session

from app.config.database import SessionLocal, engine
from app.config.settings import settings
from app.models.models import Base, Admin, ProblemStatement, EventConfig

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

PROBLEM_STATEMENTS = [
    {
        "problem_code": "PS-001",
        "title": "AI-Powered Threat Detection System",
        "description": (
            "Design an AI-based system capable of detecting cyber threats in real-time "
            "across military communication networks. The solution should handle both known "
            "and zero-day attack vectors."
        ),
        "track": "Cybersecurity & AI",
    },
    {
        "problem_code": "PS-002",
        "title": "Autonomous Border Surveillance Drone",
        "description": (
            "Develop a software stack for an autonomous UAV that can patrol a defined border "
            "perimeter, detect intrusions, and alert command centers without human intervention."
        ),
        "track": "Autonomous Systems",
    },
    {
        "problem_code": "PS-003",
        "title": "Secure Battlefield Communication Protocol",
        "description": (
            "Propose an end-to-end encrypted, low-latency communication protocol suitable "
            "for battlefield conditions, resistant to jamming and interception."
        ),
        "track": "Communications & Encryption",
    },
    {
        "problem_code": "PS-004",
        "title": "Predictive Maintenance for Military Vehicles",
        "description": (
            "Build a machine learning-based predictive maintenance system for armored vehicles "
            "that minimizes downtime and prevents field failures using sensor telemetry."
        ),
        "track": "IoT & Machine Learning",
    },
    {
        "problem_code": "PS-005",
        "title": "Soldier Health Monitoring Wearable",
        "description": (
            "Design a wearable device and companion software that continuously monitors "
            "soldier vitals (heart rate, hydration, stress) and alerts medical units in emergencies."
        ),
        "track": "Wearables & Health Tech",
    },
]


def seed():
    db: Session = SessionLocal()
    try:
        # --- Admin ---
        existing_admin = db.query(Admin).first()
        if not existing_admin:
            admin = Admin(
                email=settings.ADMIN_EMAIL,
                password_hash=pwd_context.hash("Admin@2026"),  # Change immediately in production!
                name="Admin",
            )
            db.add(admin)
            print(f"[+] Created admin: {settings.ADMIN_EMAIL} / Admin@2026")
        else:
            print("[=] Admin already exists, skipping")

        # --- Problem Statements ---
        for ps_data in PROBLEM_STATEMENTS:
            existing = db.query(ProblemStatement).filter(
                ProblemStatement.problem_code == ps_data["problem_code"]
            ).first()
            if not existing:
                db.add(ProblemStatement(**ps_data))
                print(f"[+] Added problem: {ps_data['problem_code']} — {ps_data['title']}")
            else:
                print(f"[=] Problem {ps_data['problem_code']} already exists, skipping")

        # --- Default Deadlines ---
        defaults = {
            "registration_deadline": (datetime.now(timezone.utc) + timedelta(days=30)).isoformat(),
            "submission_deadline": (datetime.now(timezone.utc) + timedelta(days=60)).isoformat(),
        }
        for key, value in defaults.items():
            existing = db.query(EventConfig).filter(EventConfig.key == key).first()
            if not existing:
                db.add(EventConfig(key=key, value=value))
                print(f"[+] Set {key} = {value}")
            else:
                print(f"[=] {key} already set, skipping")

        db.commit()
        print("\n✅ Seed complete!")
    except Exception as e:
        db.rollback()
        print(f"\n❌ Seed failed: {e}")
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    seed()
