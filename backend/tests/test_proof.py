"""Tests for Proof-of-Pwn certificate issuance + public verification."""

from __future__ import annotations

from datetime import datetime, timezone

from fastapi.testclient import TestClient

from app.core.proof import issue_certificate, verify_certificate
from app.db.session import SessionLocal
from app.models.submission import Submission
from app.models.task import Task


def test_sign_verify_roundtrip_and_tamper_detection():
    token = issue_certificate({"task_id": "t1", "score": 100})
    assert verify_certificate(token) == {"task_id": "t1", "score": 100}

    # tamper with the body -> invalid
    body, sig = token.split(".")
    tampered = body[:-2] + ("AA" if not body.endswith("AA") else "BB") + "." + sig
    assert verify_certificate(tampered) is None
    assert verify_certificate("garbage") is None


def _passed_submission(user_id: int) -> int:
    with SessionLocal() as db:
        db.add(Task(
            id="t1", title="Find the Secret", module="1", order_index=1, domain="static-re",
            masvs=["MASVS-STORAGE-1"], mastg_refs=["X"], difficulty=2, prereqs=[],
            objective="o", success_type="static_assert", submission_schema={"value": "string"},
            hints={}, is_reference=True, grader_status="implemented", package_path="tasks/t1",
        ))
        s = Submission(
            user_id=user_id, task_id="t1", success_type="static_assert", payload={"value": "x"},
            status="passed", evidence="Recovered key verified.",
            checks=[{"name": "match", "passed": True, "detail": "ok"}], score=100,
            completed_at=datetime.now(timezone.utc),
        )
        db.add(s)
        db.commit()
        return s.id


def test_certificate_endpoint_and_public_verify(client: TestClient, auth_headers):
    from app.models.user import User

    with SessionLocal() as db:
        uid = db.query(User).filter_by(email="learner@example.com").one().id
    sid = _passed_submission(uid)

    cert = client.get(f"/submissions/{sid}/certificate", headers=auth_headers)
    assert cert.status_code == 200
    body = cert.json()
    assert body["payload"]["task_title"] == "Find the Secret"
    assert body["payload"]["score"] == 100
    assert body["payload"]["evidence_sha256"]

    # public verify (no auth) confirms it
    v = client.post("/verify", json={"token": body["token"]})
    assert v.status_code == 200
    assert v.json()["valid"] is True
    assert v.json()["payload"]["learner"] == "Learner"

    # a tampered token is rejected
    bad = client.post("/verify", json={"token": body["token"][:-3] + "zzz"})
    assert bad.json()["valid"] is False


def test_certificate_only_for_passed(client: TestClient, auth_headers):
    from app.models.user import User

    with SessionLocal() as db:
        uid = db.query(User).filter_by(email="learner@example.com").one().id
        db.add(Task(
            id="t2", title="T2", module="1", order_index=2, domain="static-re",
            masvs=[], mastg_refs=[], difficulty=1, prereqs=[], objective="o",
            success_type="static_assert", submission_schema={"value": "string"}, hints={},
            is_reference=False, grader_status="implemented", package_path="tasks/t2",
        ))
        s = Submission(
            user_id=uid, task_id="t2", success_type="static_assert", payload={"value": "x"},
            status="failed", evidence="nope", checks=[], score=0,
        )
        db.add(s)
        db.commit()
        sid = s.id
    r = client.get(f"/submissions/{sid}/certificate", headers=auth_headers)
    assert r.status_code == 409
