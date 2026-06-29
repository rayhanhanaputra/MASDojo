"""OpenAI provider — Chat Completions API."""

from __future__ import annotations

import httpx
from loguru import logger

from app.services.ai.provider import AIError, AIProvider, ChatMessage

OPENAI_URL = "https://api.openai.com/v1/chat/completions"
DEFAULT_MODEL = "gpt-4o"


class OpenAIProvider(AIProvider):
    name = "openai"

    def __init__(self, api_key: str, model: str = DEFAULT_MODEL, timeout: float = 30.0) -> None:
        self._key = api_key
        self._model = model
        self._timeout = timeout

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self._key}",
            "Content-Type": "application/json",
        }

    def validate_key(self) -> bool:
        try:
            resp = httpx.post(
                OPENAI_URL,
                headers=self._headers(),
                json={
                    "model": self._model,
                    "max_tokens": 1,
                    "messages": [{"role": "user", "content": "ping"}],
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
        payload = {
            "model": self._model,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "messages": [
                {"role": "system", "content": system},
                *[{"role": m.role, "content": m.content} for m in messages],
            ],
        }
        try:
            resp = httpx.post(
                OPENAI_URL, headers=self._headers(), json=payload, timeout=self._timeout
            )
        except httpx.HTTPError as exc:
            raise AIError(f"openai request failed: {exc}") from exc

        if resp.status_code != 200:
            raise AIError(f"openai error {resp.status_code}: {_safe_error(resp)}")

        data = resp.json()
        choices = data.get("choices", [])
        if not choices:
            raise AIError("openai returned no choices")
        return (choices[0].get("message", {}).get("content") or "").strip()


def _safe_error(resp: httpx.Response) -> str:
    try:
        return resp.json().get("error", {}).get("message", resp.text[:200])
    except Exception:  # noqa: BLE001
        return resp.text[:200]
