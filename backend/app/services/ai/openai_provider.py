"""OpenAI provider — Chat Completions API."""

from __future__ import annotations

import json

import httpx
from loguru import logger

from app.core.config import settings
from app.services.ai.provider import AIError, AIProvider, ChatMessage

OPENAI_URL = "https://api.openai.com/v1/chat/completions"
DEFAULT_MODEL = "gpt-4o"


def _parse_extra_body(raw: str) -> dict:
    """Parse OPENAI_EXTRA_BODY (JSON) into a dict merged into every request.
    Invalid/empty JSON → {} (ignored), so a typo can't break the mentor."""
    raw = (raw or "").strip()
    if not raw:
        return {}
    try:
        parsed = json.loads(raw)
        return parsed if isinstance(parsed, dict) else {}
    except json.JSONDecodeError:
        logger.warning("ignoring invalid OPENAI_EXTRA_BODY (not valid JSON)")
        return {}


def _chat_url(base_url: str) -> str:
    """Resolve the Chat Completions endpoint from a configurable base URL.

    Accepts a bare origin, a `.../v1` prefix, or a full `.../v1/chat/completions`
    URL, so any OpenAI-compatible gateway/proxy can be pointed at with just its
    origin in OPENAI_BASE_URL.
    """
    b = (base_url or "https://api.openai.com").rstrip("/")
    if b.endswith("/chat/completions"):
        return b
    if b.endswith("/v1"):
        return b + "/chat/completions"
    return b + "/v1/chat/completions"


class OpenAIProvider(AIProvider):
    name = "openai"

    def __init__(
        self,
        api_key: str,
        model: str | None = None,
        # Generous enough for reasoning models behind a gateway, which can take
        # well over 30s to return a full completion.
        timeout: float = 60.0,
        base_url: str | None = None,
        extra_body: dict | None = None,
    ) -> None:
        self._key = api_key
        self._model = model or settings.openai_model or DEFAULT_MODEL
        self._timeout = timeout
        self._url = _chat_url(base_url or settings.openai_base_url)
        # Per-request extras (e.g. disable a reasoning model's slow "thinking").
        self._extra_body = (
            extra_body if extra_body is not None else _parse_extra_body(settings.openai_extra_body)
        )

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self._key}",
            "Content-Type": "application/json",
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
                    **self._extra_body,
                },
                timeout=self._timeout,
            )
        except httpx.HTTPError as exc:
            logger.warning("openai key validation network error: {}", exc)
            return False
        if resp.status_code == 200:
            return True
        # 429 covers BOTH transient rate-limiting (key is fine) and
        # insufficient_quota (exhausted credits / billing off — key is unusable).
        # Distinguish them so a dead-quota key is rejected at entry, not later.
        if resp.status_code == 429:
            try:
                err_type = resp.json().get("error", {}).get("type", "")
            except Exception:  # noqa: BLE001
                err_type = ""
            if "insufficient_quota" in err_type or "billing" in err_type:
                logger.warning("openai key rejected: {}", err_type)
                return False
            return True
        # 401/403 (auth), 404 (bad model), 400 (bad request), 5xx → reject so a
        # misconfigured key/model surfaces at entry instead of failing later.
        logger.warning("openai key validation returned {}", resp.status_code)
        return False

    def complete(
        self,
        system: str,
        messages: list[ChatMessage],
        *,
        max_tokens: int = 600,
        temperature: float = 0.3,
    ) -> str:
        # Stream the completion. Reasoning models behind a gateway (e.g. Qwen
        # "thinking" variants) can spend well over a minute generating before a
        # non-streamed response returns ANYTHING — long enough to blow the read
        # timeout and leave the mentor "hanging". Streaming flushes tokens as
        # they are produced (first byte in ~2s), so the read timeout only has to
        # cover the GAP BETWEEN chunks, not the whole generation, and we never
        # hang. We accumulate `delta.content` and ignore `reasoning_content`.
        payload = {
            "model": self._model,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "stream": True,
            "messages": [
                {"role": "system", "content": system},
                *[{"role": m.role, "content": m.content} for m in messages],
            ],
            **self._extra_body,
        }
        parts: list[str] = []
        try:
            with httpx.stream(
                "POST",
                self._url,
                headers=self._headers(),
                json=payload,
                timeout=self._timeout,
            ) as resp:
                if resp.status_code != 200:
                    resp.read()
                    raise AIError(f"openai error {resp.status_code}: {_safe_error(resp)}")
                for line in resp.iter_lines():
                    if not line or not line.startswith("data:"):
                        continue
                    chunk = line[len("data:") :].strip()
                    if chunk == "[DONE]":
                        break
                    try:
                        obj = json.loads(chunk)
                    except json.JSONDecodeError:
                        continue
                    choices = obj.get("choices") or []
                    if not choices:
                        continue
                    piece = (choices[0].get("delta") or {}).get("content")
                    if piece:
                        parts.append(piece)
        except httpx.HTTPError as exc:
            raise AIError(f"openai request failed: {exc}") from exc

        text = "".join(parts).strip()
        if not text:
            raise AIError("openai returned an empty completion")
        return text


def _safe_error(resp: httpx.Response) -> str:
    try:
        return resp.json().get("error", {}).get("message", resp.text[:200])
    except Exception:  # noqa: BLE001
        return resp.text[:200]
