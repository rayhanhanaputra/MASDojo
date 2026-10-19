"""Create database tables. Run once at startup before the seeder.

For a self-host-friendly footprint we use SQLAlchemy `create_all` rather than a
migration tool; the schema is small and additive. Swap in Alembic if/when the
schema needs versioned migrations.
"""

from __future__ import annotations

import time

from loguru import logger
from sqlalchemy import text
from sqlalchemy.exc import OperationalError

from app.core.logging import configure_logging
from app.db.base import Base
from app.db.session import engine

# Importing the models package registers every model on `Base.metadata`.
import app.models  # noqa: F401,E402


def wait_for_db(max_attempts: int = 30, delay_sec: float = 1.0) -> None:
    """Block until the database accepts connections (compose race tolerance)."""
    for attempt in range(1, max_attempts + 1):
        try:
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            return
        except OperationalError:
            logger.info("waiting for database (attempt {}/{})", attempt, max_attempts)
            time.sleep(delay_sec)
    raise RuntimeError("database did not become available in time")


# Additive column patches for existing databases (create_all won't ALTER an
# existing table). Each must be idempotent. Remove once Alembic is adopted.
_COLUMN_PATCHES = (
    "ALTER TABLE submissions ADD COLUMN IF NOT EXISTS evidence_bundle JSON DEFAULT '[]'",
    "ALTER TABLE submissions ADD COLUMN IF NOT EXISTS ai_generated BOOLEAN DEFAULT FALSE",
    "ALTER TABLE api_keys ADD COLUMN IF NOT EXISTS base_url VARCHAR(512)",
    "ALTER TABLE api_keys ADD COLUMN IF NOT EXISTS model VARCHAR(128)",
    "ALTER TABLE users ADD COLUMN IF NOT EXISTS role VARCHAR(20) NOT NULL DEFAULT 'learner'",
    "ALTER TABLE tasks ADD COLUMN IF NOT EXISTS is_published BOOLEAN NOT NULL DEFAULT TRUE",
    "ALTER TABLE tasks ADD COLUMN IF NOT EXISTS instructor_edited BOOLEAN NOT NULL DEFAULT FALSE",
    "ALTER TABLE instance_config ADD COLUMN IF NOT EXISTS lab_enabled BOOLEAN NOT NULL DEFAULT TRUE",
    "ALTER TABLE instance_config ADD COLUMN IF NOT EXISTS lab_allow_device_hosted "
    "BOOLEAN NOT NULL DEFAULT FALSE",
    "ALTER TABLE instance_config ADD COLUMN IF NOT EXISTS lab_emulator_image "
    "VARCHAR(255) NOT NULL DEFAULT ''",
    "ALTER TABLE instance_config ADD COLUMN IF NOT EXISTS lab_emulator_adb_port "
    "INTEGER NOT NULL DEFAULT 5037",
    "ALTER TABLE instance_config ADD COLUMN IF NOT EXISTS lab_emulator_serial "
    "VARCHAR(64) NOT NULL DEFAULT 'emulator-5554'",
    "ALTER TABLE instance_config ADD COLUMN IF NOT EXISTS lab_emulator_boot_timeout_sec "
    "INTEGER NOT NULL DEFAULT 180",
    "ALTER TABLE tasks ADD COLUMN IF NOT EXISTS source VARCHAR(12) NOT NULL DEFAULT 'package'",
    "ALTER TABLE tasks ADD COLUMN IF NOT EXISTS expected_override JSON",
    # One active lab session per user (defence against a create race).
    "CREATE UNIQUE INDEX IF NOT EXISTS uq_lab_active_per_user "
    "ON lab_sessions (user_id) WHERE status = 'active'",
)


def init_db() -> None:
    configure_logging()
    wait_for_db()
    logger.info("creating database tables")
    Base.metadata.create_all(bind=engine)
    # Additive patches bring an *existing* server's table up to date (create_all
    # never ALTERs). They use Postgres `ADD COLUMN IF NOT EXISTS`; on SQLite the
    # columns already exist from create_all above and that syntax is invalid, so
    # skip them there — keeping a local SQLite self-host working out of the box.
    if engine.dialect.name != "sqlite":
        # Each patch in its own transaction + best-effort, so one failure (e.g.
        # a unique index blocked by pre-existing rows) never aborts the rest.
        for stmt in _COLUMN_PATCHES:
            try:
                with engine.begin() as conn:
                    conn.execute(text(stmt))
            except Exception as exc:  # noqa: BLE001
                logger.warning("schema patch skipped: {} ({})", stmt[:60], exc)
    logger.info("database ready")


if __name__ == "__main__":
    init_db()
