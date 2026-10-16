"""Authentication routes: register, login, current user."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.config import settings
from app.core.security import create_access_token, hash_password, verify_password
from app.db.session import get_db
from app.models.user import User
from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse, UserPublic
from app.services import instance_config

router = APIRouter(prefix="/auth", tags=["auth"])


def _bootstrap_role(db: Session, email: str) -> str:
    """Decide a new user's role at registration (hosted mode bootstrap).

    Admin if the email is in ADMIN_EMAILS, or — so a fresh self-host always has
    one admin — if no user exists yet. Everyone else registers as a learner.
    """
    if email in settings.admin_email_set:
        return "admin"
    if db.scalar(select(User.id).limit(1)) is None:
        return "admin"
    return "learner"


@router.post("/register", response_model=UserPublic, status_code=status.HTTP_201_CREATED)
def register(body: RegisterRequest, db: Session = Depends(get_db)) -> User:
    email = body.email.lower()
    # Registration can be closed by an admin — but always allow the very first
    # account so a fresh instance can bootstrap its admin.
    first_user = db.scalar(select(User.id).limit(1)) is None
    if not first_user and not instance_config.registration_open(db):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Registration is closed")
    existing = db.scalar(select(User).where(User.email == email))
    if existing:
        raise HTTPException(status.HTTP_409_CONFLICT, "Email already registered")
    user = User(
        email=email,
        display_name=body.display_name,
        hashed_password=hash_password(body.password),
        role=_bootstrap_role(db, email),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.post("/login", response_model=TokenResponse)
def login(body: LoginRequest, db: Session = Depends(get_db)) -> TokenResponse:
    user = db.scalar(select(User).where(User.email == body.email.lower()))
    if not user or not verify_password(body.password, user.hashed_password):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid email or password")
    return TokenResponse(access_token=create_access_token(user.id))


@router.post("/token", response_model=TokenResponse, include_in_schema=False)
def login_form(
    form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)
) -> TokenResponse:
    """OAuth2 password-flow endpoint so the Swagger 'Authorize' button works."""
    user = db.scalar(select(User).where(User.email == form.username.lower()))
    if not user or not verify_password(form.password, user.hashed_password):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid email or password")
    return TokenResponse(access_token=create_access_token(user.id))


@router.get("/me", response_model=UserPublic)
def me(user: User = Depends(get_current_user)) -> User:
    return user
