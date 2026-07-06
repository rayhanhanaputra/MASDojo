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
)


def init_db() -> None:
    configure_logging()
    wait_for_db()
    logger.info("creating database tables")
    Base.metadata.create_all(bind=engine)
    with engine.begin() as conn:
        for stmt in _COLUMN_PATCHES:
            conn.execute(text(stmt))
    logger.info("database ready")


if __name__ == "__main__":
    init_db()
