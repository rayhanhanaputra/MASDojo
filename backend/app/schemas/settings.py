"""BYOK API-key settings models. The raw key is never returned to the client."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

Provider = Literal["anthropic", "openai"]


class ApiKeyCreate(BaseModel):
    provider: Provider
    api_key: str = Field(min_length=10, max_length=512)
    # Optional overrides for a custom OpenAI/Anthropic-compatible gateway.
    # Blank/omitted -> use the install-level default endpoint & model.
    base_url: str | None = Field(default=None, max_length=512)
    model: str | None = Field(default=None, max_length=128)


class ApiKeyStatus(BaseModel):
    """What the UI sees: provider, masked key, and (non-secret) endpoint/model."""

    model_config = ConfigDict(from_attributes=True)

    configured: bool
    provider: Provider | None = None
    masked_key: str | None = None
    base_url: str | None = None
    model: str | None = None
    last_validated_at: datetime | None = None
