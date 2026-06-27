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

    # Runner-related (read here so the backend can surface limits in the API)
    grading_job_timeout_sec: int = 420

    # Where curriculum task packages live (mounted read-only in compose).
    tasks_dir: Path = Field(default=Path("tasks"))

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
