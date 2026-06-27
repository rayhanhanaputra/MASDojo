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


def set_key(db: Session, user: User, provider: str, api_key: str) -> ApiKey:
    """Validate then persist (encrypted) the user's provider key."""
    # Validate with the user's own key before storing anything.
    if not make_provider(provider, api_key).validate_key():
        raise KeyValidationError("the provider rejected this API key")

    now = datetime.now(timezone.utc)
    record = user.api_key
    if record is None:
        record = ApiKey(user_id=user.id)
        db.add(record)
    record.provider = provider
    record.encrypted_key = encrypt_secret(api_key)
    record.masked_key = mask_key(api_key)
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
        return None
    try:
        key = decrypt_secret(record.encrypted_key)
    except ValueError:
        logger.error("could not decrypt stored key for user {}", user.id)
        return None
    return make_provider(record.provider, key)
