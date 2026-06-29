"""AI mentor routes (BYOK). Disabled gracefully when the user has no key."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from sqlalchemy import select

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.progress import Progress
from app.models.task import Task
from app.models.user import User
from app.schemas.mentor import (
    ExplainRequest,
    ExplainResponse,
    HintRequest,
    HintResponse,
    ReviewRequest,
    ReviewResponse,
)
from app.services import key_manager
from app.services.ai import mentor
from app.services.ai.provider import AIError
from app.services.ratelimit import enforce_mentor_rate_limit

router = APIRouter(prefix="/mentor", tags=["mentor"])

_NO_KEY = HTTPException(
    status.HTTP_409_CONFLICT,
    "No AI key configured. Add your Anthropic or OpenAI key in Settings to use the mentor.",
)


def _require_task(db: Session, task_id: str) -> Task:
    task = db.get(Task, task_id)
    if not task:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Task not found")
    return task


def _require_provider(db: Session, user: User):
    """Enforce the per-user rate limit, then return the user's AI provider."""
    enforce_mentor_rate_limit(user.id)
    provider = key_manager.get_provider(db, user)
    if provider is None:
        raise _NO_KEY
    return provider


@router.post("/hint", response_model=HintResponse)
def hint(
    body: HintRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> HintResponse:
    task = _require_task(db, body.task_id)
    provider = _require_provider(db, user)
    try:
        tier, text, is_solution = mentor.generate_hint(
            db, user, task, provider, body.attempt, body.error
        )
    except AIError as exc:
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, f"AI provider error: {exc}")
    return HintResponse(tier=tier, content=text, source="ai", is_solution=is_solution)


@router.post("/explain", response_model=ExplainResponse)
def explain(
    body: ExplainRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> ExplainResponse:
    task = _require_task(db, body.task_id)
    provider = _require_provider(db, user)
    try:
        text = mentor.explain_snippet(task, provider, body.snippet)
    except AIError as exc:
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, f"AI provider error: {exc}")
    return ExplainResponse(explanation=text)


@router.post("/review", response_model=ReviewResponse)
def review(
    body: ReviewRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> ReviewResponse:
    task = _require_task(db, body.task_id)
    # The post-task review is only meaningful (and only honest) after a real PASS.
    passed = db.scalar(
        select(Progress.passed).where(
            Progress.user_id == user.id,
            Progress.task_id == body.task_id,
            Progress.passed.is_(True),
        )
    )
    if not passed:
        raise HTTPException(
            status.HTTP_403_FORBIDDEN,
            "Post-task review unlocks after you pass this task.",
        )
    provider = _require_provider(db, user)
    try:
        text = mentor.post_task_review(task, provider)
    except AIError as exc:
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, f"AI provider error: {exc}")
    return ReviewResponse(review=text)
