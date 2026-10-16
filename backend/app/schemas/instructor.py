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
