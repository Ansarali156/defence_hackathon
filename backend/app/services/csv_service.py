"""
CSV export service for admin dashboard.
"""
import csv
import io
from typing import List

from sqlalchemy.orm import Session

from app.models.models import Team, Payment, Submission


def export_teams_csv(db: Session) -> str:
    """Export all teams with members to CSV string."""
    teams = db.query(Team).all()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "Team Code", "Team Name", "Category", "Team Size",
        "Lead Name", "Lead Email", "Lead Mobile",
        "Payment Status", "Payment Amount",
        "Submission Status", "Selected Problem", "Created At",
        "Member 1 Name", "Member 1 Email",
        "Member 2 Name", "Member 2 Email",
        "Member 3 Name", "Member 3 Email",
        "Member 4 Name", "Member 4 Email",
    ])
    for team in teams:
        problem = team.selected_problem.title if team.selected_problem else ""
        row = [
            team.team_code, team.team_name, team.category.value, team.team_size,
            team.lead_name, team.lead_email, team.lead_mobile,
            team.payment_status.value, float(team.payment_amount),
            team.submission_status.value, problem,
            team.created_at.isoformat(),
        ]
        for member in team.members[:4]:
            row += [member.name, member.email]
        # Pad missing member columns
        for _ in range(4 - len(team.members)):
            row += ["", ""]
        writer.writerow(row)
    return output.getvalue()


def export_payments_csv(db: Session) -> str:
    """Export all payment records."""
    payments = db.query(Payment).join(Team).all()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "Team Code", "Team Name", "Razorpay Order ID",
        "Razorpay Payment ID", "Amount", "Currency",
        "Status", "Invoice URL", "Created At",
    ])
    for p in payments:
        writer.writerow([
            p.team.team_code, p.team.team_name,
            p.razorpay_order_id or "", p.razorpay_payment_id or "",
            float(p.amount), p.currency,
            p.status.value, p.invoice_url or "",
            p.created_at.isoformat(),
        ])
    return output.getvalue()


def export_submissions_csv(db: Session) -> str:
    """Export all submissions."""
    submissions = db.query(Submission).join(Team).all()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "Team Code", "Team Name", "Problem Code", "Problem Title",
        "Abstract", "Deployment Link",
        "Project File", "Presentation File",
        "Certificate Approved", "Certificate URL", "Submitted At",
    ])
    for s in submissions:
        writer.writerow([
            s.team.team_code, s.team.team_name,
            s.problem_statement.problem_code, s.problem_statement.title,
            s.abstract[:200], s.deployment_link or "",
            s.project_file_url or "", s.presentation_url or "",
            s.certificate_approved, s.certificate_url or "",
            s.submitted_at.isoformat(),
        ])
    return output.getvalue()
