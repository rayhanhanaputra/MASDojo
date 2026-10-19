"""Admin routes: manage user accounts (list, set role, activate, delete).

All routes require the "admin" role. Admins cannot lock themselves out: an
admin may not demote or deactivate their own account, and the last remaining
active admin is protected from demotion/deactivation/deletion.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from loguru import logger
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import SOLO_EMAIL, require_role
from app.core.security import hash_password
from app.db.session import get_db
from app.models.user import User
from app.schemas.admin import (
    ActiveUpdate,
    AiFallbackCreate,
    InstanceConfigUpdate,
    InstanceConfigView,
    LabSessionAdminView,
    RoleUpdate,
    SwitchToHosted,
    SystemCheckItem,
    UserAdminView,
)
from app.services import instance_config, lab_session, system_check

router = APIRouter(prefix="/admin", tags=["admin"])


def _config_view(cfg) -> InstanceConfigView:
    return InstanceConfigView(
        solo_mode=cfg.solo_mode,
        registration_open=cfg.registration_open,
        lab_enabled=cfg.lab_enabled,
        lab_allow_device_hosted=cfg.lab_allow_device_hosted,
        lab_emulator_image=cfg.lab_emulator_image,
        lab_emulator_adb_port=cfg.lab_emulator_adb_port,
        lab_emulator_serial=cfg.lab_emulator_serial,
        lab_emulator_boot_timeout_sec=cfg.lab_emulator_boot_timeout_sec,
        lab_session_ttl_min=cfg.lab_session_ttl_min,
        lab_mem_limit=cfg.lab_mem_limit,
        lab_cpu_limit=cfg.lab_cpu_limit,
        lab_pids_limit=cfg.lab_pids_limit,
        lab_stream_url=cfg.lab_stream_url,
        grading_job_timeout_sec=cfg.grading_job_timeout_sec,
        mentor_rate_limit_per_hour=cfg.mentor_rate_limit_per_hour,
        ai_fallback_configured=bool(cfg.ai_fallback_key_encrypted),
        ai_fallback_provider=cfg.ai_fallback_provider,
        ai_fallback_masked=cfg.ai_fallback_masked,
        ai_fallback_base_url=cfg.ai_fallback_base_url,
        ai_fallback_model=cfg.ai_fallback_model,
    )


def _active_admin_count(db: Session, exclude_id: int | None = None) -> int:
    stmt = (
        select(func.count()).select_from(User).where(User.role == "admin", User.is_active.is_(True))
    )
    if exclude_id is not None:
        stmt = stmt.where(User.id != exclude_id)
    return db.scalar(stmt) or 0


def _get_or_404(db: Session, user_id: int) -> User:
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "user not found")
    return user


@router.get("/system", response_model=list[SystemCheckItem])
def system_health(
    db: Session = Depends(get_db),
    _admin: User = Depends(require_role("admin")),
) -> list[dict]:
    return system_check.run_checks(db)


@router.get("/lab/sessions", response_model=list[LabSessionAdminView])
def list_lab_sessions(
    db: Session = Depends(get_db),
    _admin: User = Depends(require_role("admin")),
) -> list[LabSessionAdminView]:
    sessions = lab_session.list_active(db)
    emails = (
        {
            u.id: u.email
            for u in db.scalars(select(User).where(User.id.in_([s.user_id for s in sessions])))
        }
        if sessions
        else {}
    )
    return [
        LabSessionAdminView(
            id=s.id,
            user_id=s.user_id,
            user_email=emails.get(s.user_id, "?"),
            task_id=s.task_id,
            device_serial=s.device_serial,
            expires_at=s.expires_at,
        )
        for s in sessions
    ]


@router.get("/settings", response_model=InstanceConfigView)
def get_settings(
    db: Session = Depends(get_db),
    _admin: User = Depends(require_role("admin")),
) -> InstanceConfigView:
    return _config_view(instance_config.get_config(db))


@router.patch("/settings", response_model=InstanceConfigView)
def update_settings(
    body: InstanceConfigUpdate,
    db: Session = Depends(get_db),
    _admin: User = Depends(require_role("admin")),
) -> InstanceConfigView:
    cfg = instance_config.get_config(db)
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(cfg, field, value)
    db.commit()
    db.refresh(cfg)
    return _config_view(cfg)


@router.post("/settings/switch-to-hosted", response_model=InstanceConfigView)
def switch_to_hosted(
    body: SwitchToHosted,
    db: Session = Depends(get_db),
    _admin: User = Depends(require_role("admin")),
) -> InstanceConfigView:
    """Switch to hosted mode, provisioning (or promoting) a real admin account
    so the operator can log in afterwards instead of being locked out."""
    email = body.email.lower()
    if email == SOLO_EMAIL:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "pick a real email, not the solo profile")
    user = db.scalar(select(User).where(User.email == email))
    if user is not None:
        # Existing account: promote + activate; keep its current password.
        user.role = "admin"
        user.is_active = True
    else:
        user = User(
            email=email,
            display_name=body.display_name,
            hashed_password=hash_password(body.password),
            role="admin",
            is_active=True,
        )
        db.add(user)
    cfg = instance_config.get_config(db)
    cfg.solo_mode = False
    db.commit()
    db.refresh(cfg)
    logger.info("switched to hosted mode; admin account {} provisioned", email)
    return _config_view(cfg)


@router.post("/settings/switch-to-solo", response_model=InstanceConfigView)
def switch_to_solo(
    db: Session = Depends(get_db),
    _admin: User = Depends(require_role("admin")),
) -> InstanceConfigView:
    """Collapse back to a single local profile with no login."""
    cfg = instance_config.get_config(db)
    cfg.solo_mode = True
    db.commit()
    db.refresh(cfg)
    logger.info("switched to solo mode")
    return _config_view(cfg)


@router.put("/settings/ai-fallback", response_model=InstanceConfigView)
def set_ai_fallback(
    body: AiFallbackCreate,
    db: Session = Depends(get_db),
    _admin: User = Depends(require_role("admin")),
) -> InstanceConfigView:
    try:
        cfg = instance_config.set_ai_fallback(
            db, body.provider, body.api_key, body.base_url, body.model
        )
    except ValueError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(exc))
    return _config_view(cfg)


@router.delete("/settings/ai-fallback", response_model=InstanceConfigView)
def clear_ai_fallback(
    db: Session = Depends(get_db),
    _admin: User = Depends(require_role("admin")),
) -> InstanceConfigView:
    return _config_view(instance_config.clear_ai_fallback(db))


@router.get("/users", response_model=list[UserAdminView])
def list_users(
    db: Session = Depends(get_db),
    _admin: User = Depends(require_role("admin")),
) -> list[User]:
    return list(db.scalars(select(User).order_by(User.id)))


@router.patch("/users/{user_id}/role", response_model=UserAdminView)
def set_role(
    user_id: int,
    body: RoleUpdate,
    db: Session = Depends(get_db),
    admin: User = Depends(require_role("admin")),
) -> User:
    user = _get_or_404(db, user_id)
    # Guard: don't strip the last admin, and don't let an admin demote itself
    # (use another admin to do that, so there's always a second pair of hands).
    if user.role == "admin" and body.role != "admin":
        if user.id == admin.id:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "cannot change your own admin role")
        if _active_admin_count(db, exclude_id=user.id) == 0:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "cannot demote the last admin")
    user.role = body.role
    db.commit()
    db.refresh(user)
    return user


@router.patch("/users/{user_id}/active", response_model=UserAdminView)
def set_active(
    user_id: int,
    body: ActiveUpdate,
    db: Session = Depends(get_db),
    admin: User = Depends(require_role("admin")),
) -> User:
    user = _get_or_404(db, user_id)
    if not body.is_active:
        if user.id == admin.id:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "cannot deactivate your own account")
        if user.role == "admin" and _active_admin_count(db, exclude_id=user.id) == 0:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "cannot deactivate the last admin")
    user.is_active = body.is_active
    db.commit()
    db.refresh(user)
    return user


@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(require_role("admin")),
) -> None:
    user = _get_or_404(db, user_id)
    if user.id == admin.id:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "cannot delete your own account")
    if user.role == "admin" and _active_admin_count(db, exclude_id=user.id) == 0:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "cannot delete the last admin")
    db.delete(user)
    db.commit()
