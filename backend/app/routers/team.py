"""
Team router — profile, problem statement listing, problem selection.
"""
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.config.database import get_db
from app.middleware.auth import get_current_team
from app.models.models import Team, ProblemStatement, PaymentStatus
from app.schemas.schemas import TeamProfileOut, ProblemStatementOut, SelectProblemRequest

router = APIRouter(prefix="/api/team", tags=["Team"])


def _get_team_or_404(db: Session, payload: dict) -> Team:
    team_id = payload["sub"]
    team = db.query(Team).filter(Team.id == team_id).first()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    return team


@router.get("/profile", response_model=TeamProfileOut)
def get_profile(
    db: Session = Depends(get_db),
    payload: dict = Depends(get_current_team),
):
    return _get_team_or_404(db, payload)


@router.get("/problem-statements", response_model=list[ProblemStatementOut])
def list_problems(
    db: Session = Depends(get_db),
    payload: dict = Depends(get_current_team),
):
    problems = db.query(ProblemStatement).filter(ProblemStatement.is_active == True).all()
    result = []
    for p in problems:
        count = db.query(func.count(Team.id)).filter(Team.selected_problem_id == p.id).scalar() or 0
        out = ProblemStatementOut(
            id=p.id,
            problem_code=p.problem_code,
            title=p.title,
            description=p.description,
            track=p.track,
            is_active=p.is_active,
            teams_selected=count,
        )
        result.append(out)
    return result


@router.post("/select-problem")
def select_problem(
    body: SelectProblemRequest,
    db: Session = Depends(get_db),
    payload: dict = Depends(get_current_team),
):
    team = _get_team_or_404(db, payload)

    if team.payment_status != PaymentStatus.SUCCESS:
        raise HTTPException(status_code=403, detail="Payment required before selecting a problem")
    if team.selected_problem_id is not None:
        raise HTTPException(status_code=409, detail="Problem already selected — selection is permanent")

    problem = db.query(ProblemStatement).filter(
        ProblemStatement.id == body.problem_id,
        ProblemStatement.is_active == True,
    ).first()
    if not problem:
        raise HTTPException(status_code=404, detail="Problem statement not found")

    # SELECT FOR UPDATE to prevent race conditions
    db.execute(
        __import__("sqlalchemy").text("SELECT id FROM teams WHERE id = :tid FOR UPDATE"),
        {"tid": str(team.id)},
    )
    # Re-check after lock
    db.refresh(team)
    if team.selected_problem_id is not None:
        raise HTTPException(status_code=409, detail="Problem already selected")

    team.selected_problem_id = body.problem_id
    db.commit()

    return {"message": f"Problem '{problem.title}' selected successfully"}


@router.get("/selected-problem", response_model=ProblemStatementOut)
def get_selected_problem(
    db: Session = Depends(get_db),
    payload: dict = Depends(get_current_team),
):
    team = _get_team_or_404(db, payload)
    if not team.selected_problem:
        raise HTTPException(status_code=404, detail="No problem selected yet")
    p = team.selected_problem
    count = db.query(func.count(Team.id)).filter(Team.selected_problem_id == p.id).scalar() or 0
    return ProblemStatementOut(
        id=p.id,
        problem_code=p.problem_code,
        title=p.title,
        description=p.description,
        track=p.track,
        is_active=p.is_active,
        teams_selected=count,
    )
