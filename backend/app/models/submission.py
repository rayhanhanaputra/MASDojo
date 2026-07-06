"""A learner's graded attempt at a task."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import JSON, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.user import User


# Submission lifecycle states.
STATUS_QUEUED = "queued"
STATUS_RUNNING = "running"
STATUS_PASSED = "passed"
STATUS_FAILED = "failed"
STATUS_ERROR = "error"


class Submission(Base, TimestampMixin):
    __tablename__ = "submissions"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    task_id: Mapped[str] = mapped_column(
        ForeignKey("tasks.id", ondelete="CASCADE"), index=True, nullable=False
    )

    success_type: Mapped[str] = mapped_column(String(20), nullable=False)
    # The learner's raw submission payload (flag string, frida script, etc.).
    payload: Mapped[dict] = mapped_column(JSON, default=dict)

    status: Mapped[str] = mapped_column(String(12), default=STATUS_QUEUED, index=True)
    # Human-readable evidence of why the grade passed/failed.
    evidence: Mapped[str] = mapped_column(Text, default="")
    # Structured per-check results: [{"name","passed","detail"}].
    checks: Mapped[list] = mapped_column(JSON, default=list)
    # Proof-of-technique evidence bundle: [{"label","kind","content"}] — the
    # flight-recorder trail (baseline/hooked logcat, traces, timeline) backing
    # the verdict. Empty for simple comparison graders.
    evidence_bundle: Mapped[list] = mapped_column(JSON, default=list)
    score: Mapped[int] = mapped_column(Integer, default=0)
    error: Mapped[str | None] = mapped_column(Text)

    # True when the payload was proposed by the AI mentor (the "AI-as-adversary"
    # loop) rather than the learner. The grader adjudicates it identically, but
    # it never affects the learner's own progress/score.
    ai_generated: Mapped[bool] = mapped_column(default=False)

    # Redis job id assigned when enqueued.
    job_id: Mapped[str | None] = mapped_column(String(64), index=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    user: Mapped["User"] = relationship(back_populates="submissions")
