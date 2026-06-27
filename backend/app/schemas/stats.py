"""Profile / stats response models."""

from __future__ import annotations

from pydantic import BaseModel


class DomainMastery(BaseModel):
    domain: str
    tasks_total: int
    tasks_passed: int
    avg_score: float
    highest_difficulty_cleared: int


class ProfileStats(BaseModel):
    display_name: str
    tasks_passed: int
    tasks_total: int
    total_score: int
    total_attempts: int
    total_hints_used: int
    domains: list[DomainMastery]
