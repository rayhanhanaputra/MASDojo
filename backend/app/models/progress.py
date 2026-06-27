"""Per-learner, per-task progress — the substrate for the pathway engine."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.user import User


class Progress(Base, TimestampMixin):
    __tablename__ = "progress"
    __table_args__ = (UniqueConstraint("user_id", "task_id", name="uq_progress_user_task"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    task_id: Mapped[str] = mapped_column(
        ForeignKey("tasks.id", ondelete="CASCADE"), index=True, nullable=False
    )

    attempts: Mapped[int] = mapped_column(Integer, default=0)
    passed: Mapped[bool] = mapped_column(Boolean, default=False)
    best_score: Mapped[int] = mapped_column(Integer, default=0)
    # Highest hint tier revealed (0 none, 1..3 hints, 4 solution).
    max_hint_tier: Mapped[int] = mapped_column(Integer, default=0)
    # Seconds from first attempt to first pass.
    time_to_solve_sec: Mapped[int | None] = mapped_column(Integer)

    domain: Mapped[str] = mapped_column(String(40), default="")
    difficulty: Mapped[int] = mapped_column(Integer, default=1)

    first_attempt_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    passed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_attempt_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    user: Mapped["User"] = relationship(back_populates="progress")
