"""Shared FastAPI dependencies: DB session and authenticated user."""

from __future__ import annotations

import secrets

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import decode_access_token, hash_password
from app.db.session import get_db
from app.models.user import User
from app.services import instance_config

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
        # Promote a solo profile created before solo users were made admins, so
        # the operator keeps full access on an upgraded instance.
        if user.role != "admin":
            user.role = "admin"
            db.commit()
            db.refresh(user)
        return user
    user = User(
        email=SOLO_EMAIL,
        display_name="You",
        # Unusable random password — solo mode never logs in with it.
        hashed_password=hash_password(secrets.token_hex(16)),
        is_active=True,
        # The solo operator owns their own instance, so they get full access
        # (admin ⊇ instructor). This replaces the old solo_mode short-circuit
        # in role checks: solo privilege is now just the solo user's role.
        role="admin",
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
    if instance_config.effective_solo_mode(db):
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


# Role hierarchy: higher rank implies every capability below it.
_ROLE_RANK = {"learner": 0, "instructor": 1, "admin": 2}


def has_min_role(user: User | None, min_role: str) -> bool:
    """True if `user` holds at least `min_role`. An anonymous caller (None) is
    treated as a learner. The solo profile is an admin (set at creation), so no
    mode special-case is needed here."""
    rank = _ROLE_RANK.get(user.role, 0) if user is not None else 0
    return rank >= _ROLE_RANK[min_role]


def get_optional_user(
    token: str | None = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User | None:
    """Like get_current_user but returns None for an anonymous caller instead of
    raising, so public catalog routes stay reachable without a token while still
    being able to tailor what they return to the viewer's role."""
    if instance_config.effective_solo_mode(db):
        return get_or_create_solo_user(db)
    if not token:
        return None
    payload = decode_access_token(token)
    if not payload or "sub" not in payload:
        return None
    try:
        user_id = int(payload["sub"])
    except (TypeError, ValueError):
        return None
    user = db.get(User, user_id)
    if user is None or not user.is_active:
        return None
    return user


def require_role(min_role: str):
    """Dependency factory: 403 unless the current user holds `min_role` or
    higher. Use as `user: User = Depends(require_role("admin"))`."""

    def _dep(user: User = Depends(get_current_user)) -> User:
        if not has_min_role(user, min_role):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"requires {min_role} role",
            )
        return user

    return _dep
