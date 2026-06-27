"""Task + skill-map response models."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class TaskSummary(BaseModel):
    """Lightweight task card for the dashboard / skill map."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    title: str
    module: str
    order_index: int
    domain: str
    masvs: list[str]
    difficulty: int
    prereqs: list[str]
    success_type: str
    time_estimate_min: int
    is_reference: bool
    grader_status: str


class TaskDetail(TaskSummary):
    """Full task view. Solutions and reference Frida scripts are never included."""

    mastg_refs: list[str]
    objective: str
    submission_schema: dict
    # Number of available canned hint tiers (1..3); solution is gated separately.
    hint_count: int


class SkillNode(BaseModel):
    """A node in the skill map with the learner's per-node state."""

    id: str
    title: str
    module: str
    domain: str
    difficulty: int
    prereqs: list[str]
    success_type: str
    masvs: list[str]
    is_reference: bool
    # "locked" | "available" | "passed"
    state: str
    best_score: int
    attempts: int


class SkillMap(BaseModel):
    nodes: list[SkillNode]
    recommended_task_id: str | None
