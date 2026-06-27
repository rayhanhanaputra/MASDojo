"""Construct an AIProvider for a given provider name + key."""

from __future__ import annotations

from app.services.ai.anthropic_provider import AnthropicProvider
from app.services.ai.openai_provider import OpenAIProvider
from app.services.ai.provider import AIProvider

SUPPORTED_PROVIDERS = ("anthropic", "openai")


def make_provider(provider: str, api_key: str) -> AIProvider:
    if provider == "anthropic":
        return AnthropicProvider(api_key)
    if provider == "openai":
        return OpenAIProvider(api_key)
    raise ValueError(f"unsupported provider '{provider}'")
