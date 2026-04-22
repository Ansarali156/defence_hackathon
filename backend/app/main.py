"""
FastAPI application entry point.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from app.config.settings import settings
from app.middleware.error_handler import (
    http_exception_handler,
    validation_exception_handler,
    generic_exception_handler,
)
from app.routers import auth, registration, payment, team, submission, admin, event

# ---------------------------------------------------------------------------
# Rate limiter
# ---------------------------------------------------------------------------
limiter = Limiter(key_func=get_remote_address)

# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------
app = FastAPI(
    title="Defense Hackathon 2026 API",
    description="Backend API for team registration, payments, submissions, and admin management.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.state.limiter = limiter

# ---------------------------------------------------------------------------
# CORS
# ---------------------------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Exception handlers
# ---------------------------------------------------------------------------
app.add_exception_handler(StarletteHTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(Exception, generic_exception_handler)
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# ---------------------------------------------------------------------------
# Routers
# ---------------------------------------------------------------------------
app.include_router(event.router)
app.include_router(registration.router)
app.include_router(payment.router)
app.include_router(auth.router)
app.include_router(team.router)
app.include_router(submission.router)
app.include_router(admin.router)

# Public problem statements (no auth)
from fastapi import Depends
from sqlalchemy.orm import Session
from app.config.database import get_db
from app.models.models import ProblemStatement


@app.get("/api/problem-statements", tags=["Public"])
def list_public_problems(db: Session = Depends(get_db)):
    problems = db.query(ProblemStatement).filter(ProblemStatement.is_active == True).all()
    return [
        {
            "id": str(p.id),
            "problem_code": p.problem_code,
            "title": p.title,
            "description": p.description,
            "track": p.track,
        }
        for p in problems
    ]


@app.get("/health", tags=["Health"])
def health_check():
    return {"status": "ok", "service": "defense-hackathon-api"}
