"""Instructor routes: manage existing curriculum tasks (hosted mode).

Instructors can list every task (including unpublished ones), edit learner-
facing presentation fields, and publish/unpublish. Editing a presentation field
marks the task `instructor_edited` so the YAML seeder stops clobbering those
fields on re-seed. Grader code, hints, and submission schema are owned by the
task package on disk and are not editable here.
"""

from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import require_role
from app.core.config import settings
from app.db.session import get_db
from app.models.task import Task
from app.models.user import User
from app.schemas.instructor import TaskManageView, TaskUpdate

router = APIRouter(prefix="/instructor", tags=["instructor"])

# Presentation/content fields an edit touches; changing any of them locks the
# task against seeder overwrite (via instructor_edited).
_PRESENTATION_FIELDS = {
    "title",
    "module",
    "order_index",
    "difficulty",
    "time_estimate_min",
    "objective",
    "hints",
}


def _material_info(task_id: str) -> tuple[bool, int]:
    """(has target APK, number of committed challenge artifacts) for a task."""
    base = (Path(settings.tasks_dir) / task_id).resolve()
    has_apk = (base / "app" / "target.apk").is_file()
    artifacts_dir = base / "artifacts"
    count = sum(1 for p in artifacts_dir.rglob("*") if p.is_file()) if artifacts_dir.is_dir() else 0
    return has_apk, count


def _view(task: Task) -> TaskManageView:
    has_apk, artifact_count = _material_info(task.id)
    return TaskManageView(
        id=task.id,
        title=task.title,
        module=task.module,
        order_index=task.order_index,
        domain=task.domain,
        difficulty=task.difficulty,
        time_estimate_min=task.time_estimate_min,
        objective=task.objective,
        success_type=task.success_type,
        grader_status=task.grader_status,
        is_reference=task.is_reference,
        is_published=task.is_published,
        instructor_edited=task.instructor_edited,
        hints=task.hints or {},
        has_target_apk=has_apk,
        artifact_count=artifact_count,
    )


@router.get("/tasks", response_model=list[TaskManageView])
def list_tasks(
    db: Session = Depends(get_db),
    _instructor: User = Depends(require_role("instructor")),
) -> list[TaskManageView]:
    tasks = db.scalars(select(Task).order_by(Task.module, Task.order_index, Task.id))
    return [_view(t) for t in tasks]


@router.patch("/tasks/{task_id}", response_model=TaskManageView)
def update_task(
    task_id: str,
    body: TaskUpdate,
    db: Session = Depends(get_db),
    _instructor: User = Depends(require_role("instructor")),
) -> TaskManageView:
    task = db.get(Task, task_id)
    if task is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "task not found")

    changes = body.model_dump(exclude_unset=True)
    if not changes:
        return _view(task)

    # Hints are merged tier-by-tier onto the existing dict so an edit to one
    # tier doesn't wipe the others.
    if "hints" in changes:
        hints = dict(task.hints or {})
        for tier, value in (changes.pop("hints") or {}).items():
            if value is not None:
                hints[tier] = value
        task.hints = hints
        changes["hints"] = hints  # so instructor_edited fires below

    for field, value in changes.items():
        setattr(task, field, value)
    # Lock edits against the YAML seeder. Toggling only is_published does not
    # count as a content edit.
    if _PRESENTATION_FIELDS & changes.keys():
        task.instructor_edited = True

    db.commit()
    db.refresh(task)
    return _view(task)
