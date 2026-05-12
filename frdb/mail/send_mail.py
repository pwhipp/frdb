from __future__ import annotations

from email.message import EmailMessage
import smtplib

from frdb.mail.config import MailConfig
from frdb.mail.exceptions import EmailDeliveryError


def send_email(to_address: str, subject: str, body: str) -> None:
    from local_settings import MAIL_CONFIG

    message = email_message(MAIL_CONFIG.sender, to_address, subject, body)
    deliver_email(MAIL_CONFIG, message)


def email_message(sender: str, to_address: str, subject: str, body: str) -> EmailMessage:
    message = EmailMessage()
    message["From"] = sender
    message["To"] = to_address
    message["Subject"] = subject
    message.set_content(body)
    return message


def deliver_email(config: MailConfig, message: EmailMessage) -> None:
    try:
        with smtplib.SMTP(config.smtp_host, config.smtp_port, timeout=config.timeout_seconds) as smtp:
            if config.use_tls:
                smtp.starttls()
            smtp.login(config.username, config.password)
            smtp.send_message(message)
    except (OSError, smtplib.SMTPException) as error:
        raise EmailDeliveryError(f"Could not send email through Amazon SES SMTP: {error}") from error
