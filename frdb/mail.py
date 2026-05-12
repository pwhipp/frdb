from __future__ import annotations

from dataclasses import dataclass
from email.message import EmailMessage
from importlib import import_module
import os
import smtplib
import sys
from types import ModuleType
from typing import Any


SES_BACKEND = "ses"
CONSOLE_BACKEND = "console"

MAIL_BACKEND_ENV = "FRDB_MAIL_BACKEND"
SES_SMTP_USERNAME_ENV = "FRDB_SES_SMTP_USERNAME"
SES_SMTP_PASSWORD_ENV = "FRDB_SES_SMTP_PASSWORD"
SES_FROM_ENV = "FRDB_SES_FROM"

LOCAL_SETTINGS_MODULE = "local_settings"
MAIL_CONFIG_SETTING = "MAIL_CONFIG"
SMTP_ENDPOINT_SETTING = "SMTP_ENDPOINT"
SMTP_PORT_SETTING = "SMTP_PORT"

SES_SMTP_HOST = "email-smtp.ap-southeast-2.amazonaws.com"
SES_SMTP_PORT = 587
SES_DEFAULT_FROM = "no-reply@qclub.au"


class EmailDeliveryError(RuntimeError):
    pass


@dataclass(frozen=True)
class MailConfig:
    backend: str = SES_BACKEND
    username: str = ""
    password: str = ""
    sender: str = SES_DEFAULT_FROM
    smtp_host: str = SES_SMTP_HOST
    smtp_port: int = SES_SMTP_PORT


def send_email(to_address: str, subject: str, body: str) -> None:
    config = mail_config()
    message = email_message(config.sender, to_address, subject, body)

    if config.backend == CONSOLE_BACKEND:
        sys.stderr.write(f"{message.as_string()}\n")
        sys.stderr.flush()
        return

    try:
        with smtplib.SMTP(config.smtp_host, config.smtp_port, timeout=15) as smtp:
            smtp.starttls()
            smtp.login(config.username, config.password)
            smtp.send_message(message)
    except (OSError, smtplib.SMTPException) as error:
        raise EmailDeliveryError(f"Could not send email through Amazon SES SMTP: {error}") from error


def email_message(sender: str, to_address: str, subject: str, body: str) -> EmailMessage:
    message = EmailMessage()
    message["From"] = sender
    message["To"] = to_address
    message["Subject"] = subject
    message.set_content(body)
    return message


def mail_config() -> MailConfig:
    settings = local_settings_module()
    config = configured_mail_config(settings)
    missing = required_config_names(config)
    if missing:
        raise EmailDeliveryError(f"Missing Amazon SES SMTP credentials: {', '.join(missing)}")

    return config


def expose_verification_codes() -> bool:
    return mail_config().backend == CONSOLE_BACKEND


def local_settings_module() -> ModuleType | None:
    try:
        return import_module(LOCAL_SETTINGS_MODULE)
    except ModuleNotFoundError as error:
        if error.name == LOCAL_SETTINGS_MODULE:
            return None
        raise


def configured_mail_config(settings: ModuleType | None) -> MailConfig:
    config = getattr(settings, MAIL_CONFIG_SETTING, None)
    if isinstance(config, MailConfig):
        return normalize_mail_config(config)

    return normalize_mail_config(MailConfig(
        backend=config_value(settings, MAIL_BACKEND_ENV, SES_BACKEND),
        username=config_value(settings, SES_SMTP_USERNAME_ENV, ""),
        password=config_value(settings, SES_SMTP_PASSWORD_ENV, ""),
        sender=config_value(settings, SES_FROM_ENV, SES_DEFAULT_FROM),
        smtp_host=config_value(settings, SMTP_ENDPOINT_SETTING, SES_SMTP_HOST),
        smtp_port=int(config_value(settings, SMTP_PORT_SETTING, SES_SMTP_PORT)),
    ))


def normalize_mail_config(config: MailConfig) -> MailConfig:
    backend = config.backend.strip().lower()
    if backend not in {SES_BACKEND, CONSOLE_BACKEND}:
        raise EmailDeliveryError(f"Unsupported email backend: {backend}")

    return MailConfig(
        backend=backend,
        username=config.username,
        password=config.password,
        sender=config.sender,
        smtp_host=config.smtp_host,
        smtp_port=config.smtp_port,
    )


def config_value(settings: ModuleType | None, name: str, default: Any) -> Any:
    if settings is not None and hasattr(settings, name):
        return getattr(settings, name)
    return os.environ.get(name, default)


def required_config_names(config: MailConfig) -> list[str]:
    if config.backend == CONSOLE_BACKEND:
        return []
    return [
        name
        for name in (SES_SMTP_USERNAME_ENV, SES_SMTP_PASSWORD_ENV)
        if not getattr(config, setting_attribute(name))
    ]


def setting_attribute(name: str) -> str:
    return {
        SES_SMTP_USERNAME_ENV: "username",
        SES_SMTP_PASSWORD_ENV: "password",
    }[name]
