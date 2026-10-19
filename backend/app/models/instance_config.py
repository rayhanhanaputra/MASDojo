"""Instance-wide configuration, editable by an admin at runtime.

A single row (id=1) holds deployment settings that an operator would otherwise
bake into `.env`: the operating mode (solo vs hosted), whether registration is
open, and an install-level AI mentor fallback. Secrets (JWT, master key, DB
URLs) stay in `.env` — only non-bootstrap, safe-to-change-at-runtime settings
live here. The AI fallback key is stored encrypted, never returned raw.
"""

from __future__ import annotations

from sqlalchemy import Boolean, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin

SINGLETON_ID = 1


class InstanceConfig(Base, TimestampMixin):
    __tablename__ = "instance_config"

    id: Mapped[int] = mapped_column(primary_key=True, default=SINGLETON_ID)

    # Operating mode. True = single local profile, no login (solo); False =
    # multi-user hosted with accounts.
    solo_mode: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    # Whether new accounts may self-register (hosted mode).
    registration_open: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    # Whether the interactive lab playground is available. On a KVM deploy this
    # is what lets learners reach the remote emulator's adb/frida shell.
    lab_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    # Admin opt-in: allow hosted lab sessions to bind a live device. Only has an
    # effect once a per-session device pool is provisioned (KVM). Until then,
    # enabling it is safe: a session simply gets no device (static analysis),
    # because the pool allocates nothing. Never falls back to an exposed bridge.
    lab_allow_device_hosted: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    # Install-level AI mentor fallback, used when a user has no personal key.
    # provider is "anthropic" | "openai"; key is encrypted at rest.
    ai_fallback_provider: Mapped[str | None] = mapped_column(String(20))
    ai_fallback_key_encrypted: Mapped[str | None] = mapped_column(String(1024))
    ai_fallback_masked: Mapped[str | None] = mapped_column(String(40))
    ai_fallback_base_url: Mapped[str | None] = mapped_column(String(512))
    ai_fallback_model: Mapped[str | None] = mapped_column(String(128))
