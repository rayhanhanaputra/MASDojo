"""Records each hint reveal, used to compute score (fewer hints = higher score)."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.user import User


class HintUsage(Base, TimestampMixin):
    __tablename__ = "hint_usage"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    task_id: Mapped[str] = mapped_column(
        ForeignKey("tasks.id", ondelete="CASCADE"), index=True, nullable=False
    )
    # 1..3 = hint tiers, 4 = full solution.
    tier: Mapped[int] = mapped_column(Integer, nullable=False)
    # "static" (canned hint file) | "ai" (mentor-generated)
    source: Mapped[str] = mapped_column(String(10), default="static")

    user: Mapped["User"] = relationship(back_populates="hint_usages")
