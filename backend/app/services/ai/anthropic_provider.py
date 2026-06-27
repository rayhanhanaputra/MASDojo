"""Anthropic provider — Claude Messages API."""

from __future__ import annotations

import httpx
from loguru import logger

from app.services.ai.provider import AIError, AIProvider, ChatMessage

ANTHROPIC_URL = "https://api.anthropic.com/v1/messages"
ANTHROPIC_VERSION = "2023-06-01"
DEFAULT_MODEL = "claude-sonnet-4-6"


class AnthropicProvider(AIProvider):
    name = "anthropic"

    def __init__(self, api_key: str, model: str = DEFAULT_MODEL, timeout: float = 30.0) -> None:
        self._key = api_key
        self._model = model
        self._timeout = timeout

    def _headers(self) -> dict[str, str]:
        return {
            "x-api-key": self._key,
            "anthropic-version": ANTHROPIC_VERSION,
            "content-type": "application/json",
        }

    def validate_key(self) -> bool:
        try:
            resp = httpx.post(
                ANTHROPIC_URL,
                headers=self._headers(),
                json={
                    "model": self._model,
                    "max_tokens": 1,
                    "messages": [{"role": "user", "content": "ping"}],
                },
                timeout=self._timeout,
            )
        except httpx.HTTPError as exc:
            logger.warning("anthropic key validation network error: {}", exc)
            return False
        if resp.status_code == 200:
            return True
        if resp.status_code in (401, 403):
            return False
        # Other errors (e.g. rate limit) don't prove the key is invalid.
        logger.warning("anthropic key validation returned {}", resp.status_code)
        return resp.status_code < 500

    def complete(
        self,
        system: str,
        messages: list[ChatMessage],
        *,
        max_tokens: int = 600,
        temperature: float = 0.3,
    ) -> str:
        payload = {
            "model": self._model,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "system": system,
            "messages": [{"role": m.role, "content": m.content} for m in messages],
        }
        try:
            resp = httpx.post(
                ANTHROPIC_URL, headers=self._headers(), json=payload, timeout=self._timeout
            )
        except httpx.HTTPError as exc:
            raise AIError(f"anthropic request failed: {exc}") from exc

        if resp.status_code != 200:
            raise AIError(f"anthropic error {resp.status_code}: {_safe_error(resp)}")

        data = resp.json()
        parts = [block.get("text", "") for block in data.get("content", []) if block.get("type") == "text"]
        return "".join(parts).strip()


def _safe_error(resp: httpx.Response) -> str:
    try:
        return resp.json().get("error", {}).get("message", resp.text[:200])
    except Exception:  # noqa: BLE001
        return resp.text[:200]
