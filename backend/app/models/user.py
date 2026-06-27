"""User account model."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import Boolean, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.api_key import ApiKey
    from app.models.hint_usage import HintUsage
    from app.models.progress import Progress
    from app.models.submission import Submission


class User(Base, TimestampMixin):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(320), unique=True, index=True, nullable=False)
    display_name: Mapped[str] = mapped_column(String(80), nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    api_key: Mapped["ApiKey | None"] = relationship(
        back_populates="user", uselist=False, cascade="all, delete-orphan"
    )
    submissions: Mapped[list["Submission"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    progress: Mapped[list["Progress"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    hint_usages: Mapped[list["HintUsage"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
