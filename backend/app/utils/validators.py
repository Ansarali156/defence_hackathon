"""
Utility: Password validation.
"""
import re


def validate_password(password: str) -> bool:
    """
    Rules:
    - Minimum 6 characters
    - At least one uppercase letter (A-Z)
    - At least one lowercase letter (a-z)
    - At least one special character (!@#$%^&* etc.)
    """
    if len(password) < 6:
        return False
    if not re.search(r"[A-Z]", password):
        return False
    if not re.search(r"[a-z]", password):
        return False
    if not re.search(r"[^a-zA-Z0-9]", password):
        return False
    return True


ALLOWED_MIME_TYPES = {
    "application/pdf",
    "application/zip",
    "application/x-zip-compressed",
    "application/vnd.ms-powerpoint",
    "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    "application/msword",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
}

MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024  # 10 MB


def validate_file(content_type: str, size: int) -> tuple[bool, str]:
    """Returns (is_valid, error_message)."""
    if content_type not in ALLOWED_MIME_TYPES:
        return False, f"File type '{content_type}' is not allowed"
    if size > MAX_FILE_SIZE_BYTES:
        return False, f"File size exceeds the 10MB limit"
    return True, ""
