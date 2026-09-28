"""Anthropic provider — Claude Messages API."""

from __future__ import annotations

import httpx
from loguru import logger

from app.core.config import settings
from app.services.ai.provider import AIError, AIProvider, ChatMessage

ANTHROPIC_URL = "https://api.anthropic.com/v1/messages"
ANTHROPIC_VERSION = "2023-06-01"
DEFAULT_MODEL = "claude-sonnet-4-6"


def _messages_url(base_url: str) -> str:
    """Resolve the Messages endpoint from a configurable base URL.

    Accepts a bare origin (`https://host`), an `.../v1` prefix, or a full
    `.../v1/messages` URL, so a custom Anthropic-compatible proxy/gateway can be
    pointed at with just its origin in ANTHROPIC_BASE_URL.
    """
    b = (base_url or "https://api.anthropic.com").rstrip("/")
    if b.endswith("/messages"):
        return b
    if b.endswith("/v1"):
        return b + "/messages"
    return b + "/v1/messages"


class AnthropicProvider(AIProvider):
    name = "anthropic"

    def __init__(
        self,
        api_key: str,
        model: str | None = None,
        timeout: float = 30.0,
        base_url: str | None = None,
    ) -> None:
        self._key = api_key
        self._model = model or settings.anthropic_model or DEFAULT_MODEL
        self._timeout = timeout
        # Custom endpoint (proxy/gateway) is install-level config; official API
        # is the default. A per-instance override is still accepted for tests.
        self._url = _messages_url(base_url or settings.anthropic_base_url)

    def _headers(self) -> dict[str, str]:
        return {
            "x-api-key": self._key,
            "anthropic-version": ANTHROPIC_VERSION,
            "content-type": "application/json",
        }

    def validate_key(self) -> bool:
        try:
            resp = httpx.post(
                self._url,
                headers=self._headers(),
                json={
                    "model": self._model,
                    "max_tokens": 1,
                    "stream": False,
                    "messages": [{"role": "user", "content": "ping"}],
                },
                timeout=self._timeout,
            )
        except httpx.HTTPError as exc:
            logger.warning("anthropic key validation network error: {}", exc)
            return False
        if resp.status_code == 200:
            return True
        # 429 = the key works but is rate-limited; treat as valid.
        if resp.status_code == 429:
            return True
        # Anything else (401/403 auth, 404 bad model, 400 bad request, 5xx) is
        # not a usable key for our purposes — reject so misconfig surfaces now
        # rather than silently failing every later mentor call.
        logger.warning("anthropic key validation returned {}", resp.status_code)
        return False

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
            "stream": False,
            "system": system,
            "messages": [{"role": m.role, "content": m.content} for m in messages],
        }
        try:
            resp = httpx.post(
                self._url, headers=self._headers(), json=payload, timeout=self._timeout
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
