"""Provider-agnostic AI interface.

One internal interface, two implementations (Anthropic, OpenAI), so additional
providers are trivial to add later. All calls are made server-side with the
requesting user's own key; keys are never logged here.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class ChatMessage:
    role: str  # "user" | "assistant"
    content: str


class AIError(RuntimeError):
    """Raised when an AI call fails (network, auth, or provider error)."""


class AIProvider(ABC):
    """Abstract chat-completion provider."""

    name: str

    @abstractmethod
    def validate_key(self) -> bool:
        """Make a cheap call to confirm the key works. False on auth failure."""

    @abstractmethod
    def complete(
        self,
        system: str,
        messages: list[ChatMessage],
        *,
        max_tokens: int = 600,
        temperature: float = 0.3,
    ) -> str:
        """Return the assistant's text completion."""
