"""Admin user-management request/response models (hosted mode)."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field

Role = Literal["learner", "instructor", "admin"]


class UserAdminView(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    display_name: str
    role: Role
    is_active: bool
    created_at: datetime


class RoleUpdate(BaseModel):
    role: Role


class ActiveUpdate(BaseModel):
    is_active: bool


# ── Instance settings (admin-configurable deployment config) ────────────────

AiProvider = Literal["anthropic", "openai"]


class SystemCheckItem(BaseModel):
    component: str
    status: Literal["ok", "warn", "down", "disabled"]
    detail: str
    hint: str = ""


class InstanceConfigView(BaseModel):
    """Deployment settings + whether an AI fallback is configured. The fallback
    key itself is never returned, only its masked form and endpoint/model."""

    solo_mode: bool
    registration_open: bool
    lab_enabled: bool
    lab_allow_device_hosted: bool
    ai_fallback_configured: bool
    ai_fallback_provider: AiProvider | None = None
    ai_fallback_masked: str | None = None
    ai_fallback_base_url: str | None = None
    ai_fallback_model: str | None = None


class InstanceConfigUpdate(BaseModel):
    # solo_mode is intentionally not settable here: switching to hosted goes
    # through /settings/switch-to-hosted (which provisions an admin), and
    # switching back to solo through /settings/switch-to-solo.
    registration_open: bool | None = None
    lab_enabled: bool | None = None
    lab_allow_device_hosted: bool | None = None


class SwitchToHosted(BaseModel):
    """Switch solo→hosted while provisioning a real admin account to log in
    with (otherwise the operator would be locked out)."""

    email: EmailStr
    display_name: str = Field(min_length=1, max_length=80)
    password: str = Field(min_length=8, max_length=128)


class AiFallbackCreate(BaseModel):
    provider: AiProvider
    api_key: str = Field(min_length=10, max_length=512)
    base_url: str | None = Field(default=None, max_length=512)
    model: str | None = Field(default=None, max_length=128)


class LabSessionAdminView(BaseModel):
    id: int
    user_id: int
    user_email: str
    task_id: str
    device_serial: str | None
    expires_at: datetime
