from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import secrets
import uuid


CODE_TTL_MINUTES = 15
CODE_TTL = timedelta(minutes=CODE_TTL_MINUTES)


@dataclass
class PendingVerification:
    code: str
    payload: dict
    expires_at: datetime


pending_verifications: dict[str, PendingVerification] = {}


def create_verification(payload: dict) -> tuple[str, str]:
    cleanup_expired()
    request_id = uuid.uuid4().hex
    code = f"{secrets.randbelow(100000):05d}"
    pending_verifications[request_id] = PendingVerification(
        code=code,
        payload=payload,
        expires_at=datetime.now(timezone.utc) + CODE_TTL,
    )
    return request_id, code


def pop_verified(request_id: str, code: str) -> dict | None:
    cleanup_expired()
    pending = pending_verifications.get(request_id)
    if pending is None or pending.code != code:
        return None
    del pending_verifications[request_id]
    return pending.payload


def cancel_verification(request_id: str) -> None:
    pending_verifications.pop(request_id, None)


def cleanup_expired() -> None:
    now = datetime.now(timezone.utc)
    expired = [
        request_id
        for request_id, pending in pending_verifications.items()
        if pending.expires_at <= now
    ]
    for request_id in expired:
        del pending_verifications[request_id]
