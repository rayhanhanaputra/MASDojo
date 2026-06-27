"""Per-user BYOK provider API key, encrypted at rest.

We persist only the Fernet ciphertext (`encrypted_key`) plus a display-safe
masked form. The plaintext is never stored, never logged, and never returned to
the client after entry.
"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.user import User


class ApiKey(Base, TimestampMixin):
    __tablename__ = "api_keys"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    # "anthropic" | "openai"
    provider: Mapped[str] = mapped_column(String(20), nullable=False)
    encrypted_key: Mapped[str] = mapped_column(String(1024), nullable=False)
    masked_key: Mapped[str] = mapped_column(String(40), nullable=False)
    last_validated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    user: Mapped["User"] = relationship(back_populates="api_key")
