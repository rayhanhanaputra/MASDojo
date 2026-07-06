"""AI mentor request/response models (BYOK)."""

from __future__ import annotations

from pydantic import BaseModel, Field


class HintRequest(BaseModel):
    task_id: str
    # The learner's current attempt / scratch work, optional.
    attempt: str = Field(default="", max_length=8000)
    # Any error output the learner is seeing.
    error: str = Field(default="", max_length=8000)


class HintResponse(BaseModel):
    tier: int
    content: str
    source: str  # "ai" | "static"
    # True when this reveal exposed the full solution.
    is_solution: bool = False


class ExplainRequest(BaseModel):
    task_id: str
    snippet: str = Field(min_length=1, max_length=12000)


class ExplainResponse(BaseModel):
    explanation: str


class ReviewRequest(BaseModel):
    task_id: str


class ReviewResponse(BaseModel):
    review: str


class AttemptRequest(BaseModel):
    task_id: str


class AttemptResponse(BaseModel):
    """The AI's proposed attempt, submitted for real grading. Poll the returned
    submission_id for the grader's verdict — the source of truth."""

    submission_id: int
    field: str  # "value" | "script"
    candidate: str  # what the AI proposed
    note: str
