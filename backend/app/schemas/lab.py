"""Lab playground request/response models."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class LabSessionView(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    task_id: str
    status: str
    device_serial: str | None = None
    expires_at: datetime
    # Visual device-screen URL (scrcpy-web / emulator WebRTC), or null for CLI
    # only. Set by the operator via LAB_STREAM_URL on a KVM runner.
    stream_url: str | None = None


class LabSessionCreate(BaseModel):
    task_id: str
