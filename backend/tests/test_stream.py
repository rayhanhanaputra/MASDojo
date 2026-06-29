"""Tests for the SSE grading-event stream: scoped-token auth + terminal replay.

We don't hold a DB session across the stream and we use a stream-scoped token
(not the account JWT). These tests verify the auth boundary and the
terminal-submission short-circuit without needing a real Redis pub/sub.
"""

from __future__ import annotations

import json

from fastapi.testclient import TestClient

from app.core.security import create_access_token, create_stream_token
from app.db.session import SessionLocal
from app.models.submission import Submission
from app.models.user import User


def _passed_submission(user_id: int) -> int:
    with SessionLocal() as db:
        s = Submission(
            user_id=user_id, task_id="t1", success_type="static_assert", payload={"value": "x"},
            status="passed", evidence="ok", checks=[], score=100,
        )
        db.add(s)
        db.commit()
        return s.id


def _uid() -> int:
    with SessionLocal() as db:
        return db.query(User).filter_by(email="learner@example.com").one().id


def test_stream_token_owner_only(client: TestClient, auth_headers):
    sid = _passed_submission(_uid())
    r = client.get(f"/submissions/{sid}/stream-token", headers=auth_headers)
    assert r.status_code == 200
    assert r.json()["token"]
    # missing submission -> 404
    assert client.get("/submissions/9999/stream-token", headers=auth_headers).status_code == 404


def test_stream_rejects_non_stream_token(client: TestClient, auth_headers):
    sid = _passed_submission(_uid())
    # a normal account JWT is not stream-scoped -> 401
    account_jwt = create_access_token(_uid())
    r = client.get(f"/submissions/{sid}/stream?token={account_jwt}")
    assert r.status_code == 401


def test_stream_rejects_token_for_other_submission(client: TestClient, auth_headers):
    sid = _passed_submission(_uid())
    wrong = create_stream_token(_uid(), sid + 1)  # sid mismatch
    assert client.get(f"/submissions/{sid}/stream?token={wrong}").status_code == 401


def test_stream_replays_and_short_circuits_when_terminal(client: TestClient, auth_headers, monkeypatch):
    sid = _passed_submission(_uid())
    token = create_stream_token(_uid(), sid)

    done = json.dumps({"ts": 1, "level": "done", "phase": "done", "msg": "verdict: PASSED"})

    class _FakeRedis:
        def lrange(self, key, a, b):
            return [
                json.dumps({"level": "info", "phase": "grade", "msg": "job picked up"}),
                done,
            ]

    monkeypatch.setattr("app.api.submissions.get_redis", lambda: _FakeRedis())
    r = client.get(f"/submissions/{sid}/stream?token={token}")
    assert r.status_code == 200
    body = r.text
    assert "job picked up" in body
    assert "verdict: PASSED" in body
