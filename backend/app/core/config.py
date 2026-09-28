"""Application configuration, loaded from environment / .env."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Typed settings sourced from environment variables.

    Mirrors the keys documented in `.env.example`.
    """

    model_config = SettingsConfigDict(env_file=".env", extra="ignore", case_sensitive=False)

    # Security
    jwt_secret: str = "change-me-to-a-long-random-hex-string"
    jwt_algorithm: str = "HS256"
    jwt_access_ttl_min: int = 120
    master_key: str = "change-me-fernet-key"

    # Database
    database_url: str = "postgresql+psycopg://masdojo:masdojo@localhost:5432/masdojo"

    # Redis / queue
    redis_url: str = "redis://localhost:6379/0"
    grading_queue: str = "masdojo:grading"

    # Backend
    backend_host: str = "0.0.0.0"
    backend_port: int = 8000
    log_level: str = "INFO"
    cors_origins: str = "http://localhost:5173"

    # Deployment mode
    # SOLO_MODE: run for a single local participant — no login, a single implicit
    # local profile, straight into the curriculum. Keep false for the multi-user
    # hosted deployment.
    solo_mode: bool = False
    # Per-install differentiator mixed into seeded-challenge seeds so each
    # participant's targets differ even in solo mode (a single fixed profile).
    # `make env` generates a random value; empty = no differentiation.
    install_salt: str = ""

    # Runner-related (read here so the backend can surface limits in the API)
    grading_job_timeout_sec: int = 420

    # Where curriculum task packages live (mounted read-only in compose).
    tasks_dir: Path = Field(default=Path("tasks"))

    # The all-in-one vulnerable target APK, served for download once built via
    # `infra/build-apps.sh vaultbank` (mounted read-only in compose).
    target_apk_path: Path = Field(default=Path("apps/vaultbank/MASDojo.apk"))

    # Escape hatch for local dev only: allow boot with the placeholder secrets.
    allow_insecure_defaults: bool = False

    # Per-user hourly cap on AI mentor calls (BYOK credit protection).
    mentor_rate_limit_per_hour: int = 30

    # ── AI mentor (BYOK) ──
    # Anthropic-compatible endpoint. Point this at a proxy/gateway (e.g. an
    # LLM router) to use a custom base URL; the provider appends `/v1/messages`.
    # Default is the official API. Env: ANTHROPIC_BASE_URL.
    anthropic_base_url: str = "https://api.anthropic.com"
    # Model id sent to the endpoint. Env: ANTHROPIC_MODEL.
    anthropic_model: str = "claude-sonnet-4-6"
    # Optional install-level Anthropic key, used as a fallback only when a user
    # has not set their own key in-app. Handy for SOLO_MODE / workshop demos so
    # the mentor works with zero UI steps. Empty = pure per-user BYOK.
    # Env: ANTHROPIC_API_KEY.
    anthropic_api_key: str = ""

    # OpenAI provider — also usable against any OpenAI-compatible gateway/proxy
    # (the provider appends `/v1/chat/completions`). Env: OPENAI_BASE_URL,
    # OPENAI_MODEL, OPENAI_API_KEY (install-level fallback key).
    openai_base_url: str = "https://api.openai.com"
    openai_model: str = "gpt-4o"
    openai_api_key: str = ""

    @property
    def mentor_fallback(self) -> tuple[str, str] | None:
        """Install-level (provider, key) fallback for the mentor, or None.

        Prefers OpenAI when an OPENAI_API_KEY is set (covers OpenAI-compatible
        gateways), else Anthropic. Only used when a user has no in-app key.
        """
        if self.openai_api_key:
            return ("openai", self.openai_api_key)
        if self.anthropic_api_key:
            return ("anthropic", self.anthropic_api_key)
        return None

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    def insecure_defaults(self) -> list[str]:
        """Return the names of any security secret still set to its placeholder."""
        bad: list[str] = []
        if self.jwt_secret == "change-me-to-a-long-random-hex-string":
            bad.append("JWT_SECRET")
        if self.master_key == "change-me-fernet-key":
            bad.append("MASTER_KEY")
        return bad

    def assert_secure(self) -> None:
        """Fail closed if shipped with placeholder secrets.

        A default MASTER_KEY makes 'encrypted at rest' meaningless (the Fernet key
        derives from a public string), and a default JWT_SECRET lets anyone forge
        tokens. Refuse to boot unless the operator explicitly opts into insecure
        defaults (ALLOW_INSECURE_DEFAULTS=true) for local development.
        """
        bad = self.insecure_defaults()
        if bad and not self.allow_insecure_defaults:
            raise RuntimeError(
                "Refusing to start with placeholder secret(s): "
                f"{', '.join(bad)}. Set them to strong random values in .env "
                "(see `make env`), or set ALLOW_INSECURE_DEFAULTS=true for local dev only."
            )


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
