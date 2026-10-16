"""Runtime instance configuration, backed by a singleton DB row.

On first access the row is created and seeded from environment defaults
(`settings`), so an existing deployment keeps behaving exactly as its `.env`
dictated until an admin changes something. After that, the DB row wins.
"""

from __future__ import annotations

from loguru import logger
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.crypto import decrypt_secret, encrypt_secret, mask_key
from app.models.instance_config import SINGLETON_ID, InstanceConfig
from app.services.ai.factory import make_provider
from app.services.ai.provider import AIProvider


def get_config(db: Session) -> InstanceConfig:
    """Return the singleton config row, creating + seeding it from env on first
    use so behaviour is unchanged until an admin edits it."""
    cfg = db.get(InstanceConfig, SINGLETON_ID)
    if cfg is not None:
        return cfg

    cfg = InstanceConfig(
        id=SINGLETON_ID,
        solo_mode=settings.solo_mode,
        registration_open=True,
        lab_enabled=settings.lab_enabled,
    )
    # Seed the AI fallback from whatever the operator put in .env, so it shows
    # up (editable) in the admin UI rather than silently living only in env.
    fb = settings.mentor_fallback
    if fb:
        provider, key = fb
        cfg.ai_fallback_provider = provider
        cfg.ai_fallback_key_encrypted = encrypt_secret(key)
        cfg.ai_fallback_masked = mask_key(key)
        if provider == "openai":
            cfg.ai_fallback_base_url = settings.openai_base_url
            cfg.ai_fallback_model = settings.openai_model
        else:
            cfg.ai_fallback_base_url = settings.anthropic_base_url
            cfg.ai_fallback_model = settings.anthropic_model
    db.add(cfg)
    db.commit()
    db.refresh(cfg)
    logger.info("seeded instance_config (solo_mode={})", cfg.solo_mode)
    return cfg


def effective_solo_mode(db: Session) -> bool:
    return get_config(db).solo_mode


def registration_open(db: Session) -> bool:
    return get_config(db).registration_open


def lab_enabled(db: Session) -> bool:
    return get_config(db).lab_enabled


def fallback_provider(db: Session) -> AIProvider | None:
    """Build the install-level mentor provider from the DB config, or None.

    Falls back to the env-configured key only if the DB row carries no key
    (it normally does, since get_config seeds it from env on first use)."""
    cfg = get_config(db)
    if cfg.ai_fallback_key_encrypted and cfg.ai_fallback_provider:
        try:
            key = decrypt_secret(cfg.ai_fallback_key_encrypted)
        except ValueError:
            logger.error("could not decrypt instance AI fallback key")
            return None
        return make_provider(
            cfg.ai_fallback_provider, key, cfg.ai_fallback_base_url, cfg.ai_fallback_model
        )
    env_fb = settings.mentor_fallback
    return make_provider(*env_fb) if env_fb else None


def set_ai_fallback(
    db: Session,
    provider: str,
    api_key: str,
    base_url: str | None,
    model: str | None,
) -> InstanceConfig:
    """Validate and store the install-level AI fallback (encrypted)."""
    base_url = (base_url or "").strip() or None
    model = (model or "").strip() or None
    if not make_provider(provider, api_key, base_url=base_url, model=model).validate_key():
        raise ValueError("the provider rejected this API key, endpoint, or model")
    cfg = get_config(db)
    cfg.ai_fallback_provider = provider
    cfg.ai_fallback_key_encrypted = encrypt_secret(api_key)
    cfg.ai_fallback_masked = mask_key(api_key)
    cfg.ai_fallback_base_url = base_url
    cfg.ai_fallback_model = model
    db.commit()
    db.refresh(cfg)
    return cfg


def clear_ai_fallback(db: Session) -> InstanceConfig:
    cfg = get_config(db)
    cfg.ai_fallback_provider = None
    cfg.ai_fallback_key_encrypted = None
    cfg.ai_fallback_masked = None
    cfg.ai_fallback_base_url = None
    cfg.ai_fallback_model = None
    db.commit()
    db.refresh(cfg)
    return cfg
