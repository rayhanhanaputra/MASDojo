"""API-level tests for auth, task catalog, hint gating, and submissions."""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.db.session import SessionLocal
from app.models.task import Task


def _seed_task(**overrides) -> None:
    defaults = dict(
        id="001-find-hardcoded-secret",
        title="Find the Hardcoded API Secret",
        module="1",
        order_index=1,
        domain="static-re",
        masvs=["MASVS-STORAGE-1"],
        mastg_refs=["MASTG-TECH-0001"],
        difficulty=2,
        prereqs=[],
        objective="Recover the embedded key.",
        success_type="static_assert",
        submission_schema={"value": "string"},
        time_estimate_min=20,
        hints={"h1": "nudge", "h2": "pointer", "h3": "steps", "solution": "FLAG{x}"},
        is_reference=True,
        grader_status="implemented",
        package_path="tasks/001-find-hardcoded-secret",
    )
    defaults.update(overrides)
    with SessionLocal() as db:
        db.add(Task(**defaults))
        db.commit()


def test_register_login_me(client: TestClient):
    r = client.post(
        "/auth/register",
        json={"email": "X@Y.com", "display_name": "Z", "password": "password123"},
    )
    assert r.status_code == 201
    assert r.json()["email"] == "x@y.com"  # normalised
    token = client.post(
        "/auth/login", json={"email": "x@y.com", "password": "password123"}
    ).json()["access_token"]
    me = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me.json()["display_name"] == "Z"


def test_tasks_listing_and_detail_excludes_solution(client: TestClient, auth_headers):
    _seed_task()
    listing = client.get("/tasks").json()
    assert len(listing) == 1
    assert "hints" not in listing[0]

    detail = client.get("/tasks/001-find-hardcoded-secret").json()
    assert detail["hint_count"] == 3
    assert "hints" not in detail  # solution/hints never inline on the detail view


def test_solution_is_gated(client: TestClient, auth_headers):
    _seed_task()
    tid = "001-find-hardcoded-secret"
    # Tier 1 hint is freely available.
    assert client.post(f"/tasks/{tid}/hints/1", headers=auth_headers).status_code == 200
    # Solution (tier 4) is locked before tier 3 / enough attempts.
    assert client.post(f"/tasks/{tid}/hints/4", headers=auth_headers).status_code == 403
    # After tier 3, the solution unlocks.
    client.post(f"/tasks/{tid}/hints/3", headers=auth_headers)
    sol = client.post(f"/tasks/{tid}/hints/4", headers=auth_headers)
    assert sol.status_code == 200
    assert sol.json()["is_solution"] is True


def test_submit_validates_payload_and_enqueues(client: TestClient, auth_headers, monkeypatch):
    _seed_task()
    tid = "001-find-hardcoded-secret"

    enqueued = {}

    def fake_enqueue(submission_id, task_id, package_path):
        enqueued["submission_id"] = submission_id
        return "job-xyz"

    monkeypatch.setattr("app.api.submissions.enqueue_grading_job", fake_enqueue)

    # Missing the required 'value' field -> 422.
    bad = client.post(f"/submissions/{tid}", json={"payload": {}}, headers=auth_headers)
    assert bad.status_code == 422

    good = client.post(
        f"/submissions/{tid}", json={"payload": {"value": "sk-123"}}, headers=auth_headers
    )
    assert good.status_code == 202
    body = good.json()
    assert body["status"] == "queued"
    assert body["job_id"] == "job-xyz"
    assert enqueued["submission_id"] == body["id"]


def test_submit_rejected_for_scaffold_grader(client: TestClient, auth_headers):
    _seed_task(grader_status="todo")
    r = client.post(
        "/submissions/001-find-hardcoded-secret",
        json={"payload": {"value": "x"}},
        headers=auth_headers,
    )
    assert r.status_code == 409
