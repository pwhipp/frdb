from pathlib import Path

from frdb.mail import MailConfig


CONTACT_RECIPIENT = "recipient@example.com"
UPLOAD_DIR = Path(__file__).resolve().parent / "uploads"

MAIL_CONFIG = MailConfig(
    smtp_host='email-smtp.replace_with_real.com',
    username="replace-with-ses-smtp-username",
    password="replace-with-ses-smtp-password",
    sender="verified-sender@example.com",
)
