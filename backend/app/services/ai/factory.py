"""Construct an AIProvider for a given provider name + key."""

from __future__ import annotations

from app.services.ai.anthropic_provider import AnthropicProvider
from app.services.ai.openai_provider import OpenAIProvider
from app.services.ai.provider import AIProvider

SUPPORTED_PROVIDERS = ("anthropic", "openai")


def make_provider(
    provider: str,
    api_key: str,
    base_url: str | None = None,
    model: str | None = None,
) -> AIProvider:
    """Build a provider. `base_url`/`model` override the install-level defaults
    (from settings) so a user can point at a custom OpenAI/Anthropic-compatible
    gateway; pass None to keep the configured default."""
    if provider == "anthropic":
        return AnthropicProvider(api_key, model=model, base_url=base_url)
    if provider == "openai":
        return OpenAIProvider(api_key, model=model, base_url=base_url)
    raise ValueError(f"unsupported provider '{provider}'")
