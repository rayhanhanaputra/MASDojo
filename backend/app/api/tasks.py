"""Task catalog routes: list, detail, gated hint reveal, and challenge files."""

from __future__ import annotations

import os
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.config import settings
from app.core.seeds import derive_seed, generate_challenge
from app.db.session import get_db
from app.models.hint_usage import HintUsage
from app.models.progress import Progress
from app.models.task import Task
from app.models.user import User
from app.schemas.mentor import HintResponse
from app.schemas.task import ArtifactEntry, TaskDetail, TaskSummary

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


def _task_dir(task_id: str) -> Path:
    return (Path(settings.tasks_dir) / task_id).resolve()


def _artifacts_root(task_id: str) -> Path:
    """The task's committed challenge files. Only `artifacts/` is ever served —
    never grader/, challenge/, frida/, hints/ (those are the answer key)."""
    return (_task_dir(task_id) / "artifacts").resolve()


def _seeded_files(task_id: str, user_id: int) -> dict[str, str] | None:
    """This learner's generated challenge files, or None if the task is static.

    For a seeded task the artifact content is unique per learner, so a value
    lifted from one learner's files never solves another's."""
    spec = generate_challenge(_task_dir(task_id), derive_seed(user_id, task_id))
    if not spec:
        return None
    return {str(k): str(v) for k, v in (spec.get("files") or {}).items()}


@router.get("/{task_id}/artifacts", response_model=list[ArtifactEntry])
def list_artifacts(
    task_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> list[ArtifactEntry]:
    """List the challenge files the learner can download/analyse for this task."""
    if not db.get(Task, task_id):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Task not found")

    seeded = _seeded_files(task_id, user.id)
    if seeded is not None:
        return [
            ArtifactEntry(path=path, size=len(content.encode()))
            for path, content in sorted(seeded.items())
        ]

    root = _artifacts_root(task_id)
    if not root.is_dir():
        return []
    return [
        ArtifactEntry(path=str(p.relative_to(root)), size=p.stat().st_size)
        for p in sorted(root.rglob("*"))
        if p.is_file()
    ]


@router.get("/{task_id}/artifacts/{artifact_path:path}")
def get_artifact(
    task_id: str,
    artifact_path: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> Response:
    """Serve one challenge file (per-learner generated for seeded tasks,
    otherwise confined to the task's artifacts/ directory)."""
    if not db.get(Task, task_id):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Task not found")

    seeded = _seeded_files(task_id, user.id)
    if seeded is not None:
        content = seeded.get(artifact_path)
        if content is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Artifact not found")
        return Response(content=content, media_type="text/plain; charset=utf-8")

    root = _artifacts_root(task_id)
    target = (root / artifact_path).resolve()
    # Path-traversal guard: the resolved target must stay inside artifacts/.
    if not (target == root or str(target).startswith(str(root) + os.sep)) or not target.is_file():
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Artifact not found")
    return Response(content=target.read_bytes(), media_type="text/plain; charset=utf-8")


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
