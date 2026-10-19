"""Lab-session lifecycle: one active, time-boxed session per user.

Allocation of a real device/serial on a KVM runner is out of scope here (that
belongs to the runner side); this service owns the bookkeeping and expiry. When
no device is allocated the terminal falls back to the placeholder shell.
"""

from __future__ import annotations

import json
import re
import time
from datetime import datetime, timedelta, timezone

from loguru import logger
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.lab_session import LabSession
from app.models.user import User
from app.services import docker_lab
from app.services.queue import get_redis

HEARTBEAT_KEY = "masdojo:runner:heartbeat"
HEARTBEAT_STALE_SEC = 25
# A valid adb serial: alphanumerics and a few separators only. Rejecting anything
# else stops a poisoned heartbeat from smuggling shell/URL metacharacters into
# the terminal command or the visual-stream URL downstream.
_SERIAL_RE = re.compile(r"^[A-Za-z0-9._:-]{1,64}$")


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _available_device() -> str | None:
    """The device serial a live (non-dry-run) runner is advertising, if any.

    This is the binding point: a new session attaches to whatever device the
    runner heartbeat reports. With a single emulator this is just that device;
    a future multi-device pool would allocate from the advertised set here.
    """
    try:
        raw = get_redis().get(HEARTBEAT_KEY)
        hb = json.loads(raw) if raw else None
    except Exception:  # noqa: BLE001
        return None
    if not hb:
        return None
    if time.time() - float(hb.get("ts", 0)) >= HEARTBEAT_STALE_SEC:
        return None
    if hb.get("mode") == "dry-run":
        return None
    device = hb.get("device")
    if device and _SERIAL_RE.match(device):
        return device
    if device:
        logger.warning("ignoring malformed device serial from heartbeat: {!r}", device)
    return None


def _expire_if_stale(db: Session, s: LabSession | None) -> LabSession | None:
    if s is None:
        return None
    expires = s.expires_at
    if expires.tzinfo is None:
        expires = expires.replace(tzinfo=timezone.utc)
    if expires <= _now():
        s.status = "expired"
        s.ended_at = _now()
        db.commit()
        docker_lab.remove_session_container(s.id)
        return None
    return s


def get_active(db: Session, user: User) -> LabSession | None:
    s = db.scalar(
        select(LabSession)
        .where(LabSession.user_id == user.id, LabSession.status == "active")
        .order_by(LabSession.id.desc())
    )
    return _expire_if_stale(db, s)


def get_for_terminal(db: Session, session_id: int, user: User) -> LabSession | None:
    """Fetch a session by id, but only if it belongs to the user and is live."""
    s = db.get(LabSession, session_id)
    if s is None or s.user_id != user.id or s.status != "active":
        return None
    return _expire_if_stale(db, s)


def create(db: Session, user: User, task_id: str) -> LabSession:
    """Return the user's live session (reused if present), else start a new one.

    One active session per user keeps device allocation simple; switching tasks
    ends the old session and starts a fresh one.
    """
    active = get_active(db, user)
    if active is not None:
        if active.task_id == task_id:
            return active
        active.status = "ended"
        active.ended_at = _now()
        db.commit()
        docker_lab.remove_session_container(active.id)

    s = LabSession(
        user_id=user.id,
        task_id=task_id,
        status="active",
        device_serial=_available_device(),
        expires_at=_now() + timedelta(minutes=settings.lab_session_ttl_min),
    )
    db.add(s)
    db.commit()
    db.refresh(s)
    logger.info(
        "lab session {} started for user {} on task {} (device={})",
        s.id,
        user.id,
        task_id,
        s.device_serial or "placeholder",
    )
    return s


def list_active(db: Session) -> list[LabSession]:
    """All currently-active sessions (admin view of who is bound to what)."""
    now = _now()
    rows = list(
        db.scalars(
            select(LabSession).where(LabSession.status == "active").order_by(LabSession.id.desc())
        )
    )
    live = []
    expired_ids = []
    for s in rows:
        exp = s.expires_at if s.expires_at.tzinfo else s.expires_at.replace(tzinfo=timezone.utc)
        if exp <= now:
            s.status = "expired"
            s.ended_at = now
            expired_ids.append(s.id)
        else:
            live.append(s)
    db.commit()
    for sid in expired_ids:
        docker_lab.remove_session_container(sid)
    return live


def reap_orphans(db: Session) -> None:
    """Remove per-session lab containers with no active session (e.g. left over
    after a backend restart)."""
    active = {s.id for s in db.scalars(select(LabSession).where(LabSession.status == "active"))}
    docker_lab.reap_orphans(active)


def end(db: Session, user: User) -> bool:
    s = get_active(db, user)
    if s is None:
        return False
    s.status = "ended"
    s.ended_at = _now()
    db.commit()
    docker_lab.remove_session_container(s.id)
    logger.info("lab session {} ended for user {}", s.id, user.id)
    return True
