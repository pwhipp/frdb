from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
import re
import time
from werkzeug.datastructures import FileStorage
from werkzeug.utils import secure_filename

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def validate_email(value: str) -> str:
    email = value.strip()
    if not EMAIL_RE.fullmatch(email):
        raise ValueError("Enter a valid email address.")
    return email


def validate_text(value: str, field_name: str, max_length: int) -> str:
    text = value.strip()
    if not text:
        raise ValueError(f"{field_name} is required.")
    if len(text) > max_length:
        raise ValueError(f"{field_name} must be {max_length} characters or fewer.")
    return text


def validate_code(value: str) -> str:
    code = value.strip()
    if not re.fullmatch(r"\d{5}", code):
        raise ValueError("Enter the five digit verification code.")
    return code


def save_verified_upload(upload: FileStorage, email: str) -> Path:
    from local_settings import UPLOAD_DIR

    if not upload or not upload.filename:
        raise ValueError("Upload an updated workbook.")

    filename = secure_filename(upload.filename)
    if not filename.lower().endswith(".xlsx"):
        raise ValueError("Upload must be an .xlsx workbook.")

    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = time.strftime("%Y%m%d-%H%M%S")
    email_prefix = secure_filename(email.split("@", 1)[0]) or "submitter"
    destination = UPLOAD_DIR / f"{timestamp}-{email_prefix}-{filename}"
    upload.save(destination)
    save_upload_metadata(destination, email)
    return destination


def save_upload_metadata(destination: Path, email: str) -> None:
    metadata = {
        "uploader_email": email,
        "uploaded_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }
    destination.with_name(f"{destination.name}.meta").write_text(
        json.dumps(metadata, indent=4) + "\n",
        encoding="utf-8",
    )
