"""An interactive lab session: a time-boxed, per-user handle on a device the
learner can drive from an in-browser terminal (adb/frida) to develop an exploit.

In hosted mode a session maps to a device/serial allocated on a KVM runner; in
solo or no-KVM setups it maps to the placeholder shell. We persist only the
bookkeeping (who, which task, which serial, lifecycle + expiry); the live
PTY/WebSocket is held in memory for the duration of the connection.
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin


class LabSession(Base, TimestampMixin):
    __tablename__ = "lab_sessions"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    task_id: Mapped[str] = mapped_column(String(120), nullable=False)
    # "active" | "ended" | "expired"
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="active")
    # Device serial on the runner host (e.g. "emulator-5554"); null = placeholder.
    device_serial: Mapped[str | None] = mapped_column(String(64))
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
