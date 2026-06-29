"""Submission request/response models."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class SubmitRequest(BaseModel):
    """The learner's submission payload. Shape depends on the task success_type:

    - flag / static_assert: {"flag": "..."} or {"value": "..."}
    - frida_assert:         {"script": "<frida js>"}
    - network_assert:       {"value": "..."}  (the intercepted value; interaction also observed live)
    """

    payload: dict = Field(default_factory=dict)


class CheckResult(BaseModel):
    name: str
    passed: bool
    detail: str = ""


class SubmissionPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    task_id: str
    success_type: str
    status: str
    evidence: str
    checks: list[CheckResult]
    score: int
    error: str | None = None
    job_id: str | None = None
    created_at: datetime
    completed_at: datetime | None = None
