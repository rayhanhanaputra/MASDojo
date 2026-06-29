"""Proof-of-Pwn certificate schemas."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel


class Certificate(BaseModel):
    token: str
    payload: dict[str, Any]


class VerifyRequest(BaseModel):
    token: str


class VerifyResponse(BaseModel):
    valid: bool
    payload: dict[str, Any] | None = None
