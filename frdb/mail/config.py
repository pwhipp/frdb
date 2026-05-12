from __future__ import annotations

from dataclasses import dataclass


SES_SMTP_HOST = "email-smtp.ap-southeast-2.amazonaws.com"
SES_SMTP_PORT = 587


@dataclass(frozen=True)
class MailConfig:
    username: str
    password: str
    sender: str
    smtp_host: str = SES_SMTP_HOST
    smtp_port: int = SES_SMTP_PORT
    use_tls: bool = True
    timeout_seconds: int = 15
