"""Curriculum task, loaded from a `task.yaml` package at seed time."""

from __future__ import annotations

from sqlalchemy import JSON, Boolean, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin


class Task(Base, TimestampMixin):
    __tablename__ = "tasks"

    # Slug id from task.yaml, e.g. "001-find-hardcoded-secret".
    id: Mapped[str] = mapped_column(String(120), primary_key=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    # Module label for grouping/ordering, e.g. "1" or "0".
    module: Mapped[str] = mapped_column(String(8), nullable=False, default="0")
    order_index: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    domain: Mapped[str] = mapped_column(String(40), nullable=False)

    masvs: Mapped[list] = mapped_column(JSON, default=list)
    mastg_refs: Mapped[list] = mapped_column(JSON, default=list)
    difficulty: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    prereqs: Mapped[list] = mapped_column(JSON, default=list)

    objective: Mapped[str] = mapped_column(Text, nullable=False, default="")
    # flag | static_assert | frida_assert | network_assert
    success_type: Mapped[str] = mapped_column(String(20), nullable=False)
    submission_schema: Mapped[dict] = mapped_column(JSON, default=dict)
    time_estimate_min: Mapped[int] = mapped_column(Integer, default=20)

    # Hint markdown keyed by tier: {"h1","h2","h3","solution"}.
    hints: Mapped[dict] = mapped_column(JSON, default=dict)

    # Whether this is one of the fully-implemented reference tasks.
    is_reference: Mapped[bool] = mapped_column(Boolean, default=False)
    # "implemented" | "todo" — whether the grader is real or a scaffold stub.
    grader_status: Mapped[str] = mapped_column(String(20), default="todo")
    # Relative path of the task package on disk (for the runner to load).
    package_path: Mapped[str] = mapped_column(String(255), default="")

    # ── Instructor-managed presentation (hosted mode) ───────────────────────
    # Visible to learners? Instructors can unpublish a task to hide it.
    is_published: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    # Set once an instructor edits presentation fields in-app. When True the
    # seeder preserves those fields on re-seed instead of clobbering them from
    # YAML (technical fields like graders/hints are still refreshed).
    instructor_edited: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # ── Instructor authoring (UI-created / overridden tasks) ────────────────
    # "package" (seeded from tasks/ on disk) | "authored" (created in-app).
    source: Mapped[str] = mapped_column(String(12), nullable=False, default="package")
    # Server-side answer key override for comparison graders (flag /
    # static_assert / network_assert). When set, the runner compares against
    # this instead of grader/expected.json, e.g. {"flag": "FLAG{...}"}. Never
    # sent to learners. NULL = use the on-disk expected.json.
    expected_override: Mapped[dict | None] = mapped_column(JSON)
