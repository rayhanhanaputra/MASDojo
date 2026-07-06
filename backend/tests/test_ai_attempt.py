"""AI-as-adversary: the mentor proposes a solution, and it is graded for real as
an ai_generated submission that never touches the learner's own progress.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

import app.api.mentor as mentor_api
from app.db.session import SessionLocal
from app.models.submission import Submission
from app.models.task import Task
from app.services.ai.provider import AIProvider, ChatMessage


class _FakeProvider(AIProvider):
    name = "anthropic"

    def __init__(self, answer: str):
        self._answer = answer

    def validate_key(self) -> bool:
        return True

    def complete(self, system, messages: list[ChatMessage], *, max_tokens=600, temperature=0.3) -> str:
        return self._answer


def _seed_task(success_type="static_assert"):
    with SessionLocal() as db:
        db.add(Task(
            id="t-ai", title="T", module="1", order_index=1, domain="static-re",
            masvs=[], mastg_refs=[], difficulty=2, prereqs=[], objective="Recover the key.",
            success_type=success_type, submission_schema={"value": "string"}, hints={},
            is_reference=False, grader_status="implemented", package_path="tasks/t-ai",
        ))
        db.commit()


@pytest.fixture(autouse=True)
def _stub_infra(monkeypatch):
    # A configured provider + no real queue.
    monkeypatch.setattr(mentor_api.key_manager, "get_provider", lambda db, user: _FakeProvider("FLAG{ai_guess}"))
    monkeypatch.setattr(mentor_api, "enforce_mentor_rate_limit", lambda uid: None)
    monkeypatch.setattr(mentor_api, "enqueue_grading_job", lambda sid, tid, pkg: "job-xyz")


def test_attempt_creates_ai_generated_submission(client: TestClient, auth_headers):
    _seed_task()
    r = client.post("/mentor/attempt", json={"task_id": "t-ai"}, headers=auth_headers)
    assert r.status_code == 200
    body = r.json()
    assert body["field"] == "value"
    assert body["candidate"] == "FLAG{ai_guess}"
    assert "grader" in body["note"].lower()

    with SessionLocal() as db:
        sub = db.get(Submission, body["submission_id"])
        assert sub is not None
        assert sub.ai_generated is True
        assert sub.payload == {"value": "FLAG{ai_guess}"}
        assert sub.job_id == "job-xyz"


def test_attempt_strips_markdown_for_frida(client: TestClient, auth_headers, monkeypatch):
    _seed_task(success_type="frida_assert")
    fenced = "```javascript\nJava.perform(function(){});\n```"
    monkeypatch.setattr(mentor_api.key_manager, "get_provider", lambda db, user: _FakeProvider(fenced))
    r = client.post("/mentor/attempt", json={"task_id": "t-ai"}, headers=auth_headers)
    assert r.status_code == 200
    assert r.json()["field"] == "script"
    assert r.json()["candidate"] == "Java.perform(function(){});"


def test_attempt_requires_key(client: TestClient, auth_headers, monkeypatch):
    _seed_task()
    monkeypatch.setattr(mentor_api.key_manager, "get_provider", lambda db, user: None)
    r = client.post("/mentor/attempt", json={"task_id": "t-ai"}, headers=auth_headers)
    assert r.status_code == 409


def test_attempt_submission_is_ai_generated_in_api(client: TestClient, auth_headers):
    _seed_task()
    sid = client.post("/mentor/attempt", json={"task_id": "t-ai"}, headers=auth_headers).json()["submission_id"]
    got = client.get(f"/submissions/{sid}", headers=auth_headers)
    assert got.status_code == 200
    assert got.json()["ai_generated"] is True
