"""Serve the all-in-one vulnerable training target (MASDojo.apk).

Public and unauthenticated on purpose: it's a deliberately-insecure practice
app with no real data, meant to be installed on the emulator. If the APK hasn't
been built yet (`infra/build-apps.sh vaultbank`), the endpoints report it's
unavailable so the UI can hide the download.
"""

from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from app.core.config import settings

router = APIRouter(tags=["downloads"])


def _apk_path() -> Path:
    return Path(settings.target_apk_path).resolve()


@router.get("/download/target-apk/status")
def target_apk_status() -> dict[str, object]:
    """Whether the target APK is available, and its size."""
    apk = _apk_path()
    if apk.is_file():
        return {"available": True, "filename": "MASDojo.apk", "size": apk.stat().st_size}
    return {"available": False, "filename": "MASDojo.apk", "size": 0}


@router.get("/download/target-apk")
def download_target_apk() -> FileResponse:
    """Download the all-in-one vulnerable target app."""
    apk = _apk_path()
    if not apk.is_file():
        raise HTTPException(404, "Target APK not built yet (run infra/build-apps.sh vaultbank)")
    return FileResponse(
        apk,
        media_type="application/vnd.android.package-archive",
        filename="MASDojo.apk",
    )
