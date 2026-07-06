"""Solo mode: a single local participant, no login. /config advertises it, and
protected routes resolve the implicit local profile without any token — while
hosted mode still requires auth.
"""

from __future__ import annotations

import os

from fastapi.testclient import TestClient

from app.api.deps import SOLO_EMAIL
from app.core import seeds
from app.core.config import settings


def test_config_reports_mode(client: TestClient):
    assert client.get("/config").json()["solo_mode"] is False


def test_hosted_mode_requires_auth(client: TestClient):
    # No token, hosted mode -> 401.
    assert client.get("/auth/me").status_code == 401


def test_solo_mode_resolves_local_user_without_token(client: TestClient, monkeypatch):
    monkeypatch.setattr(settings, "solo_mode", True)
    assert client.get("/config").json()["solo_mode"] is True

    me = client.get("/auth/me")  # no Authorization header
    assert me.status_code == 200
    assert me.json()["email"] == SOLO_EMAIL

    # The same profile is reused, not recreated, on subsequent calls.
    again = client.get("/auth/me")
    assert again.json()["id"] == me.json()["id"]


def test_install_salt_differentiates_seeds(monkeypatch):
    monkeypatch.delenv("INSTALL_SALT", raising=False)
    base = seeds.derive_seed(1, "t")

    monkeypatch.setenv("INSTALL_SALT", "install-A")
    a = seeds.derive_seed(1, "t")

    monkeypatch.setenv("INSTALL_SALT", "install-B")
    b = seeds.derive_seed(1, "t")

    # Different installs -> different targets for the same profile+task.
    assert len({base, a, b}) == 3
    # Deterministic within an install.
    monkeypatch.setenv("INSTALL_SALT", "install-A")
    assert seeds.derive_seed(1, "t") == a
    assert os.environ["INSTALL_SALT"] == "install-A"
