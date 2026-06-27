"""Tests for BYOK key management (encrypted at rest) and the AI mentor.

Provider network calls are stubbed so tests are hermetic — we assert on the
encryption-at-rest invariant, the masked-only exposure, graceful no-key
behaviour, and the mentor's hint-tier escalation + solution gating.
"""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.core.crypto import decrypt_secret
from app.db.session import SessionLocal
from app.models.api_key import ApiKey
from app.models.progress import Progress
from app.models.task import Task
from app.services.ai.provider import AIProvider, ChatMessage


class _FakeProvider(AIProvider):
    name = "anthropic"

    def __init__(self, valid: bool = True):
        self._valid = valid

    def validate_key(self) -> bool:
        return self._valid

    def complete(self, system, messages: list[ChatMessage], *, max_tokens=600, temperature=0.3) -> str:
        return f"[hint about: {messages[-1].content[:24]}]"


def _seed_task(**overrides):
    defaults = dict(
        id="t1",
        title="Task One",
        module="1",
        order_index=1,
        domain="static-re",
        masvs=["MASVS-STORAGE-1"],
        mastg_refs=["MASTG-TECH-0011"],
        difficulty=2,
        prereqs=[],
        objective="Recover the key.",
        success_type="static_assert",
        submission_schema={"value": "string"},
        hints={},
        is_reference=True,
        grader_status="implemented",
        package_path="tasks/t1",
    )
    defaults.update(overrides)
    with SessionLocal() as db:
        db.add(Task(**defaults))
        db.commit()


def test_key_stored_encrypted_and_only_masked_is_returned(client: TestClient, auth_headers, monkeypatch):
    monkeypatch.setattr("app.services.key_manager.make_provider", lambda p, k: _FakeProvider(True))

    raw = "sk-ant-supersecret-0123456789"
    r = client.put("/settings/ai-key", json={"provider": "anthropic", "api_key": raw}, headers=auth_headers)
    assert r.status_code == 200
    body = r.json()
    assert body["configured"] is True
    assert body["provider"] == "anthropic"
    # The raw key is never echoed back; only a masked form.
    assert raw not in str(body)
    assert body["masked_key"].endswith("6789")

    # At rest it is ciphertext, not the raw key — but decryptable server-side.
    with SessionLocal() as db:
        record = db.query(ApiKey).one()
        assert record.encrypted_key != raw
        assert decrypt_secret(record.encrypted_key) == raw


def test_invalid_key_is_rejected(client: TestClient, auth_headers, monkeypatch):
    monkeypatch.setattr("app.services.key_manager.make_provider", lambda p, k: _FakeProvider(False))
    r = client.put("/settings/ai-key", json={"provider": "openai", "api_key": "sk-bad-000000"}, headers=auth_headers)
    assert r.status_code == 400


def test_remove_key(client: TestClient, auth_headers, monkeypatch):
    monkeypatch.setattr("app.services.key_manager.make_provider", lambda p, k: _FakeProvider(True))
    client.put("/settings/ai-key", json={"provider": "anthropic", "api_key": "sk-ant-abcdef123456"}, headers=auth_headers)
    assert client.delete("/settings/ai-key", headers=auth_headers).status_code == 204
    assert client.get("/settings/ai-key", headers=auth_headers).json()["configured"] is False


def test_mentor_disabled_without_key(client: TestClient, auth_headers):
    _seed_task()
    r = client.post("/mentor/hint", json={"task_id": "t1"}, headers=auth_headers)
    assert r.status_code == 409  # graceful: prompts the user to add a key


def test_mentor_hint_escalates_and_gates_solution(client: TestClient, auth_headers, monkeypatch):
    _seed_task()
    monkeypatch.setattr("app.services.key_manager.get_provider", lambda db, user: _FakeProvider(True))

    # First three calls escalate tiers 1 -> 2 -> 3.
    tiers = []
    for _ in range(3):
        resp = client.post("/mentor/hint", json={"task_id": "t1"}, headers=auth_headers).json()
        tiers.append(resp["tier"])
        assert resp["source"] == "ai"
    assert tiers == [1, 2, 3]

    # The fourth (solution) tier is now unlocked because tier 3 was reached.
    resp = client.post("/mentor/hint", json={"task_id": "t1"}, headers=auth_headers).json()
    assert resp["tier"] == 4
    assert resp["is_solution"] is True
