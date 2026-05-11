from __future__ import annotations

from dataclasses import dataclass
from email.message import EmailMessage
import os
import smtplib


class EmailDeliveryError(RuntimeError):
    pass


@dataclass(frozen=True)
class MailConfig:
    host: str
    port: int
    username: str
    password: str
    sender: str
    use_tls: bool


def send_email(to_address: str, subject: str, body: str) -> None:
    config = mail_config()
    message = EmailMessage()
    message["From"] = config.sender
    message["To"] = to_address
    message["Subject"] = subject
    message.set_content(body)

    try:
        with smtplib.SMTP(config.host, config.port, timeout=15) as smtp:
            if config.use_tls:
                smtp.starttls()
            smtp.login(config.username, config.password)
            smtp.send_message(message)
    except OSError as error:
        raise EmailDeliveryError("Could not send email with the configured SMTP settings") from error


def mail_config() -> MailConfig:
    missing = [
        name
        for name in ("FRDB_SMTP_HOST", "FRDB_SMTP_USERNAME", "FRDB_SMTP_PASSWORD", "FRDB_SMTP_FROM")
        if not os.environ.get(name)
    ]
    if missing:
        raise EmailDeliveryError(f"Missing SMTP configuration: {', '.join(missing)}")

    return MailConfig(
        host=os.environ["FRDB_SMTP_HOST"],
        port=int(os.environ.get("FRDB_SMTP_PORT", "587")),
        username=os.environ["FRDB_SMTP_USERNAME"],
        password=os.environ["FRDB_SMTP_PASSWORD"],
        sender=os.environ["FRDB_SMTP_FROM"],
        use_tls=os.environ.get("FRDB_SMTP_USE_TLS", "true").lower() != "false",
    )
