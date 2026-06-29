"""Tests for the security-hardening quick-win.

Covers: fail-closed startup guard on placeholder secrets, mentor rate limiting,
the post-task review PASS gate, and validate_key rejecting a bad-model 404.
"""

from __future__ import annotations

from datetime import datetime, timezone

import httpx
import pytest
from fastapi.testclient import TestClient

from app.core.config import Settings
from app.db.session import SessionLocal
from app.models.progress import Progress
from app.models.task import Task
from app.models.user import User
from app.services.ai.anthropic_provider import AnthropicProvider
from app.services.ai.provider import AIProvider, ChatMessage


# ── startup guard ─────────────────────────────────────────────────────────────
def test_assert_secure_rejects_default_secrets():
    s = Settings(
        jwt_secret="change-me-to-a-long-random-hex-string",
        master_key="change-me-fernet-key",
        allow_insecure_defaults=False,
    )
    assert set(s.insecure_defaults()) == {"JWT_SECRET", "MASTER_KEY"}
    with pytest.raises(RuntimeError):
        s.assert_secure()


def test_assert_secure_allows_with_optin_and_real_secrets():
    Settings(
        jwt_secret="change-me-to-a-long-random-hex-string",
        master_key="change-me-fernet-key",
        allow_insecure_defaults=True,
    ).assert_secure()  # opt-in -> no raise
    Settings(jwt_secret="a" * 64, master_key="real-key").assert_secure()  # real -> no raise


# ── shared fakes ──────────────────────────────────────────────────────────────
class _FakeProvider(AIProvider):
    name = "anthropic"

    def validate_key(self) -> bool:
        return True

    def complete(self, system, messages: list[ChatMessage], *, max_tokens=600, temperature=0.3):
        return "review text"


class _FakeRedis:
    def __init__(self):
        self.store: dict[str, int] = {}

    def set(self, key, val, ex=None, nx=False):
        if nx and key in self.store:
            return None
        self.store[key] = int(val)
        return True

    def incr(self, key):
        self.store[key] = self.store.get(key, 0) + 1
        return self.store[key]

    def expire(self, key, ttl):
        return True


def _seed_task(passed_by: int | None = None):
    with SessionLocal() as db:
        db.add(Task(
            id="t1", title="T", module="1", order_index=1, domain="static-re",
            masvs=["MASVS-STORAGE-1"], mastg_refs=["X"], difficulty=2, prereqs=[],
            objective="o", success_type="static_assert", submission_schema={"value": "string"},
            hints={}, is_reference=True, grader_status="implemented", package_path="tasks/t1",
        ))
        if passed_by is not None:
            db.add(Progress(
                user_id=passed_by, task_id="t1", domain="static-re", difficulty=2,
                attempts=1, passed=True, best_score=100, passed_at=datetime.now(timezone.utc),
            ))
        db.commit()


def _uid(email="learner@example.com"):
    with SessionLocal() as db:
        return db.query(User).filter_by(email=email).one().id


# ── mentor review PASS gate ───────────────────────────────────────────────────
def test_review_requires_pass(client: TestClient, auth_headers, monkeypatch):
    _seed_task()
    monkeypatch.setattr("app.api.mentor.key_manager.get_provider", lambda db, u: _FakeProvider())
    # not passed -> 403
    r = client.post("/mentor/review", json={"task_id": "t1"}, headers=auth_headers)
    assert r.status_code == 403

    # mark passed -> allowed
    _make_passed(_uid())
    r = client.post("/mentor/review", json={"task_id": "t1"}, headers=auth_headers)
    assert r.status_code == 200
    assert r.json()["review"] == "review text"


def _make_passed(user_id: int):
    with SessionLocal() as db:
        db.add(Progress(
            user_id=user_id, task_id="t1", domain="static-re", difficulty=2,
            attempts=1, passed=True, best_score=100, passed_at=datetime.now(timezone.utc),
        ))
        db.commit()


# ── mentor rate limit ─────────────────────────────────────────────────────────
def test_mentor_rate_limit(client: TestClient, auth_headers, monkeypatch):
    _seed_task()
    monkeypatch.setattr("app.api.mentor.key_manager.get_provider", lambda db, u: _FakeProvider())
    monkeypatch.setattr("app.services.ratelimit.get_redis", lambda: _FakeRedis.instance)
    _FakeRedis.instance = _FakeRedis()
    monkeypatch.setattr("app.services.ratelimit.settings.mentor_rate_limit_per_hour", 2)

    codes = [
        client.post("/mentor/explain", json={"task_id": "t1", "snippet": "x"}, headers=auth_headers).status_code
        for _ in range(3)
    ]
    assert codes[0] == 200 and codes[1] == 200
    assert codes[2] == 429  # third call over the limit of 2


# ── validate_key rejects bad-model 404 ────────────────────────────────────────
def test_validate_key_rejects_404(monkeypatch):
    def fake_post(url, headers=None, json=None, timeout=None):
        return httpx.Response(404, json={"error": {"message": "model not found"}})

    monkeypatch.setattr(httpx, "post", fake_post)
    assert AnthropicProvider("sk-ant-test").validate_key() is False


def test_validate_key_accepts_200(monkeypatch):
    def fake_post(url, headers=None, json=None, timeout=None):
        return httpx.Response(200, json={"content": [{"type": "text", "text": "ok"}]})

    monkeypatch.setattr(httpx, "post", fake_post)
    assert AnthropicProvider("sk-ant-test").validate_key() is True
