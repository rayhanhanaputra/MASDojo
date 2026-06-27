"""Task catalog routes: list, detail, and gated hint reveal."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.hint_usage import HintUsage
from app.models.progress import Progress
from app.models.task import Task
from app.models.user import User
from app.schemas.mentor import HintResponse
from app.schemas.task import TaskDetail, TaskSummary

router = APIRouter(prefix="/tasks", tags=["tasks"])

# A learner may unlock the full solution after this many failed attempts even
# without walking every hint tier first.
SOLUTION_ATTEMPT_THRESHOLD = 3
HINT_KEYS = {1: "h1", 2: "h2", 3: "h3", 4: "solution"}


def _hint_count(task: Task) -> int:
    return sum(1 for k in ("h1", "h2", "h3") if task.hints.get(k))


@router.get("", response_model=list[TaskSummary])
def list_tasks(db: Session = Depends(get_db)) -> list[Task]:
    return list(
        db.scalars(select(Task).order_by(Task.module, Task.order_index, Task.id)).all()
    )


@router.get("/{task_id}", response_model=TaskDetail)
def get_task(task_id: str, db: Session = Depends(get_db)) -> TaskDetail:
    task = db.get(Task, task_id)
    if not task:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Task not found")
    return TaskDetail(
        **{c.name: getattr(task, c.name) for c in Task.__table__.columns if c.name != "hints"},
        hint_count=_hint_count(task),
    )


@router.post("/{task_id}/hints/{tier}", response_model=HintResponse)
def reveal_hint(
    task_id: str,
    tier: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> HintResponse:
    """Reveal a static hint tier (1..3) or the gated solution (4)."""
    if tier not in HINT_KEYS:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "tier must be 1, 2, 3, or 4")

    task = db.get(Task, task_id)
    if not task:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Task not found")

    key = HINT_KEYS[tier]
    content = task.hints.get(key)
    if not content:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"No hint available at tier {tier}")

    progress = db.scalar(
        select(Progress).where(Progress.user_id == user.id, Progress.task_id == task_id)
    )
    attempts = progress.attempts if progress else 0

    is_solution = tier == 4
    if is_solution:
        unlocked = (progress and progress.max_hint_tier >= 3) or attempts >= SOLUTION_ATTEMPT_THRESHOLD
        if not unlocked:
            raise HTTPException(
                status.HTTP_403_FORBIDDEN,
                "Solution is locked until you've used hint tier 3 or made "
                f"{SOLUTION_ATTEMPT_THRESHOLD} attempts.",
            )

    # Record the reveal and bump the learner's max tier for scoring.
    db.add(HintUsage(user_id=user.id, task_id=task_id, tier=tier, source="static"))
    if progress is None:
        progress = Progress(
            user_id=user.id,
            task_id=task_id,
            domain=task.domain,
            difficulty=task.difficulty,
            max_hint_tier=tier,
        )
        db.add(progress)
    else:
        progress.max_hint_tier = max(progress.max_hint_tier, tier)
    db.commit()

    return HintResponse(tier=tier, content=content, source="static", is_solution=is_solution)
