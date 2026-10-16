"""Instructor task-management request/response models (hosted mode).

Instructors manage presentation and availability of existing tasks; they do not
author graders (those are code packages on disk). Editable fields are the
learner-facing metadata plus the published flag.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class TaskManageView(BaseModel):
    """Full management row: everything an instructor needs to see, including
    unpublished tasks and the technical fields they cannot edit."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    title: str
    module: str
    order_index: int
    domain: str
    difficulty: int
    time_estimate_min: int
    objective: str
    success_type: str
    grader_status: str
    is_reference: bool
    is_published: bool
    instructor_edited: bool
    source: str = "package"
    submission_schema: dict = Field(default_factory=dict)
    # Server-side answer key (staff-only; never exposed to learners). Empty when
    # the task grades from its on-disk expected.json or a seeded generator.
    expected_value: str = ""
    # Step-by-step answer key the instructor can review/edit.
    hints: dict = Field(default_factory=dict)
    # Read-only challenge-material info.
    has_target_apk: bool = False
    artifact_count: int = 0


class HintsUpdate(BaseModel):
    h1: str | None = Field(default=None, max_length=20000)
    h2: str | None = Field(default=None, max_length=20000)
    h3: str | None = Field(default=None, max_length=20000)
    solution: str | None = Field(default=None, max_length=40000)


class TaskUpdate(BaseModel):
    """Partial update of an existing task's presentation / availability.

    Every field is optional; only the ones provided are changed.
    """

    title: str | None = Field(default=None, min_length=1, max_length=200)
    module: str | None = Field(default=None, max_length=8)
    order_index: int | None = Field(default=None, ge=0)
    difficulty: int | None = Field(default=None, ge=1, le=5)
    time_estimate_min: int | None = Field(default=None, ge=1, le=600)
    objective: str | None = Field(default=None, max_length=20000)
    is_published: bool | None = None
    # Edit the step-by-step hints / solution. Only the provided tiers change.
    hints: HintsUpdate | None = None
    # Set/clear the server-side answer key (stored as {"value": ...}). "" clears.
    expected_value: str | None = Field(default=None, max_length=4000)
    # Change the grading type / submission shape (guardrailed in the API).
    success_type: str | None = None
    submission_schema: dict | None = None


_SLUG = r"^[a-z0-9]+(?:-[a-z0-9]+)*$"
_AUTHORABLE_TYPES = ("flag", "static_assert")


class TaskCreate(BaseModel):
    """Create a new instructor-authored task. Only data-driven grading types are
    allowed (flag / static_assert); device-driven tasks need a code grader."""

    id: str = Field(pattern=_SLUG, min_length=3, max_length=120)
    title: str = Field(min_length=1, max_length=200)
    module: str = Field(max_length=8)
    domain: str = Field(min_length=1, max_length=40)
    success_type: str = Field(default="flag")
    objective: str = Field(default="", max_length=20000)
    difficulty: int = Field(default=1, ge=1, le=5)
    time_estimate_min: int = Field(default=20, ge=1, le=600)
    masvs: list[str] = Field(default_factory=list)
    order_index: int = Field(default=0, ge=0)
    submission_schema: dict = Field(default_factory=lambda: {"flag": "string"})
    expected_value: str = Field(min_length=1, max_length=4000)
    hints: HintsUpdate | None = None
