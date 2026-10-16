"""Instructor routes: manage existing curriculum tasks (hosted mode).

Instructors can list every task (including unpublished ones), edit learner-
facing presentation fields, and publish/unpublish. Editing a presentation field
marks the task `instructor_edited` so the YAML seeder stops clobbering those
fields on re-seed. Grader code, hints, and submission schema are owned by the
task package on disk and are not editable here.
"""

from __future__ import annotations

import zipfile

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from loguru import logger
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import require_role
from app.db.session import get_db
from app.models.task import Task
from app.models.user import User
from app.schemas.instructor import (
    _AUTHORABLE_TYPES,
    TaskCreate,
    TaskManageView,
    TaskUpdate,
)
from app.services import task_assets

router = APIRouter(prefix="/instructor", tags=["instructor"])

# Grading types the UI understands. Authored tasks are limited to the data-driven
# ones; editing an existing task's type is restricted to these too.
_VALID_SUCCESS_TYPES = ("flag", "static_assert", "frida_assert", "network_assert")
_MAX_APK_BYTES = 200 * 1024 * 1024


def _expected_value_of(task: Task) -> str:
    ov = task.expected_override or {}
    return str(ov.get("value") or ov.get("flag") or ov.get("secret") or "")


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
    """(has target APK, number of committed challenge artifacts) for a task.

    Resolves store-first so an uploaded APK / authored task reports correctly."""
    try:
        has_apk = task_assets.apk_path(task_id) is not None
        adir = task_assets.artifacts_dir(task_id)
        count = sum(1 for p in adir.rglob("*") if p.is_file()) if adir.is_dir() else 0
    except task_assets.UnsafeTaskId:
        return False, 0
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
        source=task.source,
        submission_schema=task.submission_schema or {},
        expected_value=_expected_value_of(task),
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

    # Answer-key override: stored as {"value": ...}; blank clears it.
    if "expected_value" in changes:
        val = (changes.pop("expected_value") or "").strip()
        task.expected_override = {"value": val} if val else None

    if "success_type" in changes:
        st = changes.pop("success_type")
        if st not in _VALID_SUCCESS_TYPES:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, f"invalid success_type {st!r}")
        # Switching a package task to a device type it has no code grader for
        # would never pass, so only allow data-driven types unless the task
        # already ships that grader on disk.
        if st not in _AUTHORABLE_TYPES and task.source == "authored":
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST,
                f"authored tasks support {' / '.join(_AUTHORABLE_TYPES)} only",
            )
        task.success_type = st

    for field, value in changes.items():
        setattr(task, field, value)
    # Lock edits against the YAML seeder. Toggling only is_published does not
    # count as a content edit.
    _LOCKING = _PRESENTATION_FIELDS | {"expected_value", "success_type", "submission_schema"}
    if _LOCKING & (body.model_dump(exclude_unset=True)).keys():
        task.instructor_edited = True

    db.commit()
    db.refresh(task)
    return _view(task)


@router.post("/tasks", response_model=TaskManageView, status_code=status.HTTP_201_CREATED)
def create_task(
    body: TaskCreate,
    db: Session = Depends(get_db),
    _instructor: User = Depends(require_role("instructor")),
) -> TaskManageView:
    """Create an instructor-authored, data-driven task (flag / static_assert).

    The answer key lives in the DB; add a target APK afterwards via the upload
    endpoint. Device-driven tasks (frida/network) need a code grader and can't
    be authored from the UI."""
    if body.success_type not in _AUTHORABLE_TYPES:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            f"authored tasks support {' / '.join(_AUTHORABLE_TYPES)} only",
        )
    if db.get(Task, body.id) is not None:
        raise HTTPException(status.HTTP_409_CONFLICT, "a task with this id already exists")

    hints = {}
    if body.hints is not None:
        hints = {k: v for k, v in body.hints.model_dump().items() if v}

    task = Task(
        id=body.id,
        title=body.title,
        module=body.module,
        order_index=body.order_index,
        domain=body.domain,
        masvs=body.masvs,
        difficulty=body.difficulty,
        objective=body.objective,
        success_type=body.success_type,
        submission_schema=body.submission_schema,
        time_estimate_min=body.time_estimate_min,
        hints=hints,
        grader_status="implemented",
        source="authored",
        instructor_edited=True,
        is_published=False,  # draft until the instructor publishes
        expected_override={"value": body.expected_value.strip()},
        package_path="",
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    logger.info("instructor authored task {}", task.id)
    return _view(task)


@router.delete("/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(
    task_id: str,
    db: Session = Depends(get_db),
    _instructor: User = Depends(require_role("instructor")),
) -> None:
    """Delete an instructor-authored task. Package tasks can't be deleted here
    (the seeder would recreate them); unpublish those instead."""
    task = db.get(Task, task_id)
    if task is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "task not found")
    if task.source != "authored":
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            "only authored tasks can be deleted; unpublish a package task instead",
        )
    db.delete(task)
    db.commit()
    logger.info("instructor deleted authored task {}", task_id)


@router.post("/tasks/{task_id}/apk", response_model=TaskManageView)
def upload_apk(
    task_id: str,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    _instructor: User = Depends(require_role("instructor")),
) -> TaskManageView:
    """Upload/replace a task's target APK into the writable task-store."""
    task = db.get(Task, task_id)
    if task is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "task not found")

    data = file.file.read(_MAX_APK_BYTES + 1)
    if len(data) > _MAX_APK_BYTES:
        raise HTTPException(status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, "APK exceeds 200 MB")
    # Validate it's really an APK: a zip containing AndroidManifest.xml.
    import io

    try:
        with zipfile.ZipFile(io.BytesIO(data)) as zf:
            names = zf.namelist()
    except zipfile.BadZipFile:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "not a valid APK (not a zip archive)")
    if "AndroidManifest.xml" not in names:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "not a valid APK (no AndroidManifest.xml)")

    dest = task_assets.upload_apk_target(task_id)
    dest.write_bytes(data)
    logger.info("instructor uploaded APK for {} ({} bytes)", task_id, len(data))
    return _view(task)
