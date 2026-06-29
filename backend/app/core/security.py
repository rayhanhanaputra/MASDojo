"""Password hashing and JWT issuance/verification."""

from __future__ import annotations

import base64
import hashlib
from datetime import datetime, timedelta, timezone
from typing import Any

import bcrypt
from jose import JWTError, jwt

from app.core.config import settings


def _prepare(password: str) -> bytes:
    """Pre-hash to a fixed length so passwords longer than bcrypt's 72-byte
    limit are supported without silent truncation."""
    digest = hashlib.sha256(password.encode("utf-8")).digest()
    return base64.b64encode(digest)


def hash_password(password: str) -> str:
    return bcrypt.hashpw(_prepare(password), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(_prepare(plain), hashed.encode("utf-8"))
    except ValueError:
        return False


def create_access_token(subject: str | int, extra: dict[str, Any] | None = None) -> str:
    now = datetime.now(timezone.utc)
    payload: dict[str, Any] = {
        "sub": str(subject),
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=settings.jwt_access_ttl_min)).timestamp()),
    }
    if extra:
        payload.update(extra)
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def create_stream_token(user_id: int, submission_id: int, ttl_sec: int = 300) -> str:
    """A short-lived, single-purpose token for the SSE stream (EventSource can't
    send headers, so it travels in the URL — keep it narrow and short-lived)."""
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user_id),
        "scope": "stream",
        "sid": submission_id,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(seconds=ttl_sec)).timestamp()),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> dict[str, Any] | None:
    """Return the token payload, or None if invalid/expired."""
    try:
        return jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
    except JWTError:
        return None
