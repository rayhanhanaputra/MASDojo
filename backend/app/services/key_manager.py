"""BYOK API-key management.

Stores each user's provider key encrypted at rest, validates it with a cheap
provider call before saving, exposes only a masked form to the UI, and builds an
AIProvider on demand for server-side mentor calls. The raw key is never logged
and never returned to the client after entry.
"""

from __future__ import annotations

from datetime import datetime, timezone

from loguru import logger
from sqlalchemy.orm import Session

from app.core.crypto import decrypt_secret, encrypt_secret, mask_key
from app.models.api_key import ApiKey
from app.models.user import User
from app.services.ai.factory import make_provider
from app.services.ai.provider import AIProvider


class KeyValidationError(RuntimeError):
    """Raised when a submitted key fails provider validation."""


def get_record(db: Session, user: User) -> ApiKey | None:
    return user.api_key


def set_key(
    db: Session,
    user: User,
    provider: str,
    api_key: str,
    base_url: str | None = None,
    model: str | None = None,
) -> ApiKey:
    """Validate then persist (encrypted) the user's provider key.

    `base_url`/`model` are optional overrides for a custom OpenAI/Anthropic-
    compatible gateway (e.g. an LLM router like elelem). Blank strings are
    normalised to None so the install-level default is used instead.
    """
    base_url = (base_url or "").strip() or None
    model = (model or "").strip() or None
    # Validate against the *same* endpoint/model we will store, so a bad gateway
    # URL or a model the gateway doesn't serve is rejected at entry, not later.
    if not make_provider(provider, api_key, base_url=base_url, model=model).validate_key():
        raise KeyValidationError("the provider rejected this API key, endpoint, or model")

    now = datetime.now(timezone.utc)
    record = user.api_key
    if record is None:
        record = ApiKey(user_id=user.id)
        db.add(record)
    record.provider = provider
    record.encrypted_key = encrypt_secret(api_key)
    record.masked_key = mask_key(api_key)
    record.base_url = base_url
    record.model = model
    record.last_validated_at = now
    db.commit()
    db.refresh(record)
    logger.info("stored {} key for user {} (masked {})", provider, user.id, record.masked_key)
    return record


def remove_key(db: Session, user: User) -> bool:
    record = user.api_key
    if record is None:
        return False
    db.delete(record)
    db.commit()
    logger.info("removed AI key for user {}", user.id)
    return True


def get_provider(db: Session, user: User) -> AIProvider | None:
    """Build an AIProvider from the user's stored key, or None if unset.

    Returns None (rather than raising) so callers can degrade AI features
    gracefully when no key is configured.
    """
    record = user.api_key
    if record is None:
        # Install-level fallback: when the user hasn't set their own key in-app,
        # use the admin-configured instance fallback (or the env default it was
        # seeded from) so the mentor works out of the box. Per-user BYOK still
        # takes precedence. Imported lazily to avoid an import cycle.
        from app.services import instance_config

        return instance_config.fallback_provider(db)
    try:
        key = decrypt_secret(record.encrypted_key)
    except ValueError:
        logger.error("could not decrypt stored key for user {}", user.id)
        return None
    return make_provider(record.provider, key, base_url=record.base_url, model=record.model)
