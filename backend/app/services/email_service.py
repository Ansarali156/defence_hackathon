"""
Email service using SendGrid SMTP-compatible API via fastapi-mail.
"""
import logging
from pathlib import Path

from fastapi_mail import FastMail, MessageSchema, ConnectionConfig, MessageType

from app.config.settings import settings

logger = logging.getLogger(__name__)

conf = ConnectionConfig(
    MAIL_USERNAME=settings.EMAIL_FROM,
    MAIL_PASSWORD=settings.SENDGRID_API_KEY,
    MAIL_FROM=settings.EMAIL_FROM,
    MAIL_FROM_NAME=settings.EMAIL_FROM_NAME,
    MAIL_PORT=587,
    MAIL_SERVER="smtp.sendgrid.net",
    MAIL_STARTTLS=True,
    MAIL_SSL_TLS=False,
    USE_CREDENTIALS=True,
    VALIDATE_CERTS=True,
)

fm = FastMail(conf)


async def send_registration_confirmation(
    to_email: str, team_name: str, team_code: str, payment_amount: int
):
    body = f"""
    <h2>Welcome to Defense Hackathon 2026!</h2>
    <p>Dear {team_name},</p>
    <p>Your registration has been received. Please complete payment to confirm your spot.</p>
    <ul>
      <li><strong>Team Code:</strong> {team_code}</li>
      <li><strong>Amount Due:</strong> ₹{payment_amount}</li>
    </ul>
    <p>Use your team code and registered email to log in at any time.</p>
    """
    message = MessageSchema(
        subject="Defense Hackathon 2026 — Registration Received",
        recipients=[to_email],
        body=body,
        subtype=MessageType.html,
    )
    try:
        await fm.send_message(message)
    except Exception as exc:
        logger.error("Failed to send registration email to %s: %s", to_email, exc)


async def send_payment_confirmation(
    to_email: str, team_name: str, team_code: str, amount: int
):
    body = f"""
    <h2>Payment Confirmed — Defense Hackathon 2026</h2>
    <p>Dear {team_name},</p>
    <p>Your payment of <strong>₹{amount}</strong> has been successfully processed.</p>
    <p><strong>Team Code:</strong> {team_code}</p>
    <p>Log in to your dashboard to select a problem statement and submit your project.</p>
    """
    message = MessageSchema(
        subject="Defense Hackathon 2026 — Payment Confirmed",
        recipients=[to_email],
        body=body,
        subtype=MessageType.html,
    )
    try:
        await fm.send_message(message)
    except Exception as exc:
        logger.error("Failed to send payment email to %s: %s", to_email, exc)


async def send_password_set_confirmation(to_email: str, team_name: str):
    body = f"""
    <h2>Password Set Successfully</h2>
    <p>Dear {team_name},</p>
    <p>Your Defense Hackathon 2026 password has been set successfully.</p>
    <p>If you did not perform this action, please contact us immediately.</p>
    """
    message = MessageSchema(
        subject="Your Defense Hackathon 2026 Password Has Been Set Successfully",
        recipients=[to_email],
        body=body,
        subtype=MessageType.html,
    )
    try:
        await fm.send_message(message)
    except Exception as exc:
        logger.error("Failed to send password-set email to %s: %s", to_email, exc)


async def send_password_reset_email(to_email: str, reset_link: str):
    body = f"""
    <h2>Reset Your Password</h2>
    <p>Click the link below to reset your password. This link is valid for 1 hour.</p>
    <p><a href="{reset_link}">{reset_link}</a></p>
    <p>If you did not request a password reset, please ignore this email.</p>
    """
    message = MessageSchema(
        subject="Defense Hackathon 2026 — Password Reset Request",
        recipients=[to_email],
        body=body,
        subtype=MessageType.html,
    )
    try:
        await fm.send_message(message)
    except Exception as exc:
        logger.error("Failed to send reset email to %s: %s", to_email, exc)


async def send_certificate_ready_email(to_email: str, team_name: str, certificate_url: str):
    body = f"""
    <h2>Your Certificate is Ready!</h2>
    <p>Dear {team_name},</p>
    <p>Your participation certificate for Defense Hackathon 2026 is ready for download.</p>
    <p><a href="{certificate_url}">Download Certificate</a></p>
    """
    message = MessageSchema(
        subject="Defense Hackathon 2026 — Your Certificate is Ready",
        recipients=[to_email],
        body=body,
        subtype=MessageType.html,
    )
    try:
        await fm.send_message(message)
    except Exception as exc:
        logger.error("Failed to send certificate email to %s: %s", to_email, exc)
