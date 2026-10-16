"""Resolve a task's on-disk assets (target APK, challenge artifacts).

Instructor-authored or APK-overridden tasks live in the writable task-store;
everything else lives in the read-only tasks/ package dir. The store always
wins when a file is present there, so an uploaded APK or a new authored task
transparently overrides the committed package.
"""

from __future__ import annotations

from pathlib import Path

from app.core.config import settings


def store_dir(task_id: str) -> Path:
    return (Path(settings.task_store_dir) / task_id).resolve()


def package_dir(task_id: str) -> Path:
    return (Path(settings.tasks_dir) / task_id).resolve()


def apk_path(task_id: str) -> Path | None:
    """The task's target APK: uploaded override first, then the package copy."""
    for base in (store_dir(task_id), package_dir(task_id)):
        candidate = base / "app" / "target.apk"
        if candidate.is_file():
            return candidate
    return None


def artifacts_dir(task_id: str) -> Path:
    """Where this task's committed challenge files live (store override first)."""
    store = store_dir(task_id) / "artifacts"
    if store.is_dir():
        return store
    return package_dir(task_id) / "artifacts"


def upload_apk_target(task_id: str) -> Path:
    """Destination path for an uploaded APK (created under the writable store)."""
    dest = store_dir(task_id) / "app" / "target.apk"
    dest.parent.mkdir(parents=True, exist_ok=True)
    return dest
