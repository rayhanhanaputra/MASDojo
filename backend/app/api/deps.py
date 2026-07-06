"""Shared FastAPI dependencies: DB session and authenticated user."""

from __future__ import annotations

import secrets

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import decode_access_token, hash_password
from app.db.session import get_db
from app.models.user import User

# auto_error=False so solo mode can resolve a user without any token.
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login", auto_error=False)

# The single implicit profile used in SOLO_MODE (one local participant).
SOLO_EMAIL = "solo@masdojo.dev"

_CREDENTIALS_EXC = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Could not validate credentials",
    headers={"WWW-Authenticate": "Bearer"},
)


def get_or_create_solo_user(db: Session) -> User:
    """The single local profile for solo mode, created on first use."""
    user = db.scalar(select(User).where(User.email == SOLO_EMAIL))
    if user is not None:
        return user
    user = User(
        email=SOLO_EMAIL,
        display_name="You",
        # Unusable random password — solo mode never logs in with it.
        hashed_password=hash_password(secrets.token_hex(16)),
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def get_current_user(
    token: str | None = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    # Solo mode: a single local participant, no login required.
    if settings.solo_mode:
        return get_or_create_solo_user(db)

    if not token:
        raise _CREDENTIALS_EXC
    payload = decode_access_token(token)
    if not payload or "sub" not in payload:
        raise _CREDENTIALS_EXC
    try:
        user_id = int(payload["sub"])
    except (TypeError, ValueError):
        raise _CREDENTIALS_EXC
    user = db.get(User, user_id)
    if user is None or not user.is_active:
        raise _CREDENTIALS_EXC
    return user
