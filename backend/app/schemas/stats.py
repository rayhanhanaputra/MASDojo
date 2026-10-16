"""Profile / stats response models."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class DomainMastery(BaseModel):
    domain: str
    tasks_total: int
    tasks_passed: int
    avg_score: float
    highest_difficulty_cleared: int


class ModuleProgress(BaseModel):
    module: str
    tasks_total: int
    tasks_passed: int


class TaskStat(BaseModel):
    """Per-task progress for a learner."""

    task_id: str
    title: str
    module: str
    domain: str
    difficulty: int
    success_type: str
    # "passed" | "attempted" | "not_started"
    status: str
    best_score: int
    attempts: int
    hint_tier_used: int
    time_to_solve_sec: int | None = None
    last_activity: datetime | None = None
    passed_at: datetime | None = None


class ProfileStats(BaseModel):
    display_name: str
    tasks_passed: int
    tasks_total: int
    total_score: int
    total_attempts: int
    total_hints_used: int
    # ── richer summary ──
    tasks_attempted: int = 0
    completion_pct: float = 0.0
    pass_rate: float = 0.0  # passed / attempted
    avg_attempts_per_pass: float = 0.0
    highest_difficulty_cleared: int = 0
    avg_time_to_solve_min: float = 0.0
    masvs_covered: list[str] = []
    first_active: datetime | None = None
    last_active: datetime | None = None
    domains: list[DomainMastery] = []
    modules: list[ModuleProgress] = []
    tasks: list[TaskStat] = []


class RosterEntry(BaseModel):
    """One row in the staff roster: a learner and their headline progress."""

    id: int
    email: str
    display_name: str
    role: str
    tasks_passed: int
    tasks_total: int
    total_score: int
