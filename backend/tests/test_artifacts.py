"""Tests for challenge-file serving: only artifacts/ is exposed, never the
answer key (grader/expected.json, hints/solution, frida/), and no traversal.
"""

from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from app.core.config import settings
from app.db.session import SessionLocal
from app.models.task import Task


def _seed_task_on_disk(tasks_dir: Path, tid: str) -> None:
    pkg = tasks_dir / tid
    (pkg / "artifacts" / "res" / "values").mkdir(parents=True)
    (pkg / "artifacts" / "strings.xml").write_text("<resources>FLAG{x}</resources>")
    (pkg / "artifacts" / "res" / "values" / "notes.txt").write_text("note")
    # answer-key files that must NEVER be served
    (pkg / "grader").mkdir()
    (pkg / "grader" / "expected.json").write_text('{"value": "SECRET-ANSWER"}')
    (pkg / "hints").mkdir()
    (pkg / "hints" / "solution.md").write_text("the answer is SECRET-ANSWER")
    with SessionLocal() as db:
        db.add(Task(
            id=tid, title="T", module="1", order_index=1, domain="static-re",
            masvs=[], mastg_refs=[], difficulty=1, prereqs=[], objective="o",
            success_type="static_assert", submission_schema={"value": "string"}, hints={},
            is_reference=False, grader_status="implemented", package_path=f"tasks/{tid}",
        ))
        db.commit()


def test_list_and_serve_artifacts(client: TestClient, auth_headers, tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "tasks_dir", tmp_path)
    _seed_task_on_disk(tmp_path, "t-art")

    listing = client.get("/tasks/t-art/artifacts", headers=auth_headers)
    assert listing.status_code == 200
    paths = {e["path"] for e in listing.json()}
    assert paths == {"strings.xml", "res/values/notes.txt"}
    # the answer key is not listed
    assert not any("expected" in p or "solution" in p for p in paths)

    got = client.get("/tasks/t-art/artifacts/strings.xml", headers=auth_headers)
    assert got.status_code == 200
    assert "FLAG{x}" in got.text

    nested = client.get("/tasks/t-art/artifacts/res/values/notes.txt", headers=auth_headers)
    assert nested.status_code == 200 and nested.text == "note"


def test_answer_key_is_never_served(client: TestClient, auth_headers, tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "tasks_dir", tmp_path)
    _seed_task_on_disk(tmp_path, "t-sec")

    # traversal out of artifacts/ into the grader / solution never leaks the
    # answer — whether blocked by URL normalization (405/404) or by our guard.
    for evil in [
        "../grader/expected.json",
        "../hints/solution.md",
        "../../t-sec/grader/expected.json",
    ]:
        r = client.get(f"/tasks/t-sec/artifacts/{evil}", headers=auth_headers)
        assert r.status_code != 200, f"{evil} should not succeed"
        assert "SECRET-ANSWER" not in r.text

    # A `..` segment that reaches our handler intact is rejected by the guard.
    guarded = client.get(
        "/tasks/t-sec/artifacts/res/..%2F..%2Fgrader%2Fexpected.json", headers=auth_headers
    )
    assert guarded.status_code == 404
    assert "SECRET-ANSWER" not in guarded.text


def test_artifacts_require_auth_and_real_task(client: TestClient, auth_headers, tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "tasks_dir", tmp_path)
    assert client.get("/tasks/t-art/artifacts").status_code == 401  # no token
    assert client.get("/tasks/nope/artifacts", headers=auth_headers).status_code == 404
