"""Test fixtures. Uses a throwaway SQLite database so tests need no services."""

from __future__ import annotations

import os
import tempfile
from pathlib import Path

# Configure the environment BEFORE importing any app module so the engine binds
# to SQLite rather than the production Postgres URL.
_tmp_db = Path(tempfile.gettempdir()) / "masdojo_test.sqlite3"
os.environ.setdefault("DATABASE_URL", f"sqlite+pysqlite:///{_tmp_db}")
os.environ.setdefault("MASTER_KEY", "test-master-key")
os.environ.setdefault("JWT_SECRET", "test-jwt-secret")

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

import app.models  # noqa: E402,F401  (register models)
from app.db.base import Base  # noqa: E402
from app.db.session import engine  # noqa: E402
from app.main import app  # noqa: E402


@pytest.fixture(autouse=True)
def _fresh_db():
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    yield
    Base.metadata.drop_all(engine)


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


@pytest.fixture
def auth_headers(client: TestClient) -> dict[str, str]:
    client.post(
        "/auth/register",
        json={"email": "learner@example.com", "display_name": "Learner", "password": "password123"},
    )
    token = client.post(
        "/auth/login", json={"email": "learner@example.com", "password": "password123"}
    ).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
