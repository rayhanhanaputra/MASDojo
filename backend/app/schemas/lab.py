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


class LabSessionCreate(BaseModel):
    task_id: str
