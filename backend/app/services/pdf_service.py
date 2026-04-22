"""
PDF generation for participation certificates using ReportLab.
"""
import io
from datetime import datetime

from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.enums import TA_CENTER


def generate_certificate(
    team_name: str,
    team_code: str,
    problem_title: str,
    submitted_at: datetime,
) -> bytes:
    """
    Generate a participation certificate PDF and return as bytes.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=landscape(A4),
        rightMargin=inch,
        leftMargin=inch,
        topMargin=0.75 * inch,
        bottomMargin=0.75 * inch,
    )

    styles = getSampleStyleSheet()
    center = ParagraphStyle("center", parent=styles["Normal"], alignment=TA_CENTER)
    title_style = ParagraphStyle(
        "title",
        parent=styles["Title"],
        fontSize=36,
        textColor=colors.HexColor("#1a2c4e"),
        alignment=TA_CENTER,
        spaceAfter=12,
    )
    subtitle_style = ParagraphStyle(
        "subtitle",
        fontSize=16,
        textColor=colors.HexColor("#4a6fa5"),
        alignment=TA_CENTER,
        spaceAfter=6,
    )
    body_style = ParagraphStyle(
        "body",
        fontSize=13,
        alignment=TA_CENTER,
        spaceAfter=4,
    )
    team_style = ParagraphStyle(
        "team",
        fontSize=24,
        textColor=colors.HexColor("#1a2c4e"),
        alignment=TA_CENTER,
        fontName="Helvetica-Bold",
    )

    story = [
        Spacer(1, 0.3 * inch),
        Paragraph("CERTIFICATE OF PARTICIPATION", title_style),
        Paragraph("Defense Hackathon 2026", subtitle_style),
        Spacer(1, 0.3 * inch),
        Paragraph("This is to certify that the team", body_style),
        Spacer(1, 0.1 * inch),
        Paragraph(team_name, team_style),
        Spacer(1, 0.1 * inch),
        Paragraph(f"(Team Code: {team_code})", body_style),
        Spacer(1, 0.2 * inch),
        Paragraph("successfully participated and submitted their project on the problem statement:", body_style),
        Spacer(1, 0.1 * inch),
        Paragraph(f"<b>{problem_title}</b>", body_style),
        Spacer(1, 0.2 * inch),
        Paragraph(
            f"Submitted on: {submitted_at.strftime('%d %B %Y')}",
            body_style,
        ),
        Spacer(1, 0.4 * inch),
        Paragraph("____________________________", center),
        Paragraph("Organising Committee", center),
        Paragraph("Defense Hackathon 2026", center),
    ]

    doc.build(story)
    buffer.seek(0)
    return buffer.read()


def generate_payment_invoice(
    team_name: str,
    team_code: str,
    amount: int,
    payment_id: str,
    paid_at: datetime,
) -> bytes:
    """Generate a simple payment invoice PDF."""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=inch, leftMargin=inch)

    styles = getSampleStyleSheet()
    center = ParagraphStyle("center", parent=styles["Normal"], alignment=TA_CENTER)

    story = [
        Paragraph("<b>Defense Hackathon 2026</b>", center),
        Paragraph("Payment Invoice", center),
        Spacer(1, 0.3 * inch),
        Table(
            [
                ["Team Name", team_name],
                ["Team Code", team_code],
                ["Payment ID", payment_id],
                ["Amount Paid", f"₹ {amount}"],
                ["Date", paid_at.strftime("%d %B %Y %H:%M UTC")],
                ["Status", "PAID"],
            ],
            colWidths=[2.5 * inch, 4 * inch],
        ),
    ]

    doc.build(story)
    buffer.seek(0)
    return buffer.read()
