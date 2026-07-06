"""Seeded artifact serving: each learner is served their own generated files,
so a secret lifted from one learner's artifact can't solve another's task.
"""

from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from app.core.config import settings
from app.db.session import SessionLocal
from app.models.task import Task

_GENERATOR = '''
import random
def generate(seed):
    rng = random.Random(seed)
    token = "tok_" + "".join(rng.choice("0123456789abcdef") for _ in range(24))
    return {
        "answer": token,
        "files": {"shared_prefs/auth.xml": f"<map><string name='t'>{token}</string></map>"},
        "present_in": ["shared_prefs/auth.xml"],
    }
'''


def _seed_task(tasks_dir: Path, tid: str) -> None:
    pkg = tasks_dir / tid
    (pkg / "challenge").mkdir(parents=True)
    (pkg / "challenge" / "generate.py").write_text(_GENERATOR)
    with SessionLocal() as db:
        db.add(Task(
            id=tid, title="T", module="2", order_index=1, domain="storage",
            masvs=[], mastg_refs=[], difficulty=2, prereqs=[], objective="o",
            success_type="static_assert", submission_schema={"value": "string"}, hints={},
            is_reference=False, grader_status="implemented", package_path=f"tasks/{tid}",
        ))
        db.commit()


def _register(client: TestClient, email: str) -> dict[str, str]:
    client.post("/auth/register", json={"email": email, "display_name": email, "password": "password123"})
    token = client.post("/auth/login", json={"email": email, "password": "password123"}).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_each_learner_gets_a_distinct_seeded_file(client: TestClient, tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "tasks_dir", tmp_path)
    _seed_task(tmp_path, "t-seed")
    a = _register(client, "a@example.com")
    b = _register(client, "b@example.com")

    # Both learners see the same file path...
    listing = client.get("/tasks/t-seed/artifacts", headers=a)
    assert listing.status_code == 200
    assert [e["path"] for e in listing.json()] == ["shared_prefs/auth.xml"]

    # ...but different content (different embedded token).
    file_a = client.get("/tasks/t-seed/artifacts/shared_prefs/auth.xml", headers=a).text
    file_b = client.get("/tasks/t-seed/artifacts/shared_prefs/auth.xml", headers=b).text
    assert file_a != file_b, "distinct learners must be served distinct artifacts"

    # And it's stable for the same learner across requests.
    file_a2 = client.get("/tasks/t-seed/artifacts/shared_prefs/auth.xml", headers=a).text
    assert file_a == file_a2

    # A path not in the generated set 404s (no traversal to real files).
    assert client.get("/tasks/t-seed/artifacts/../grader/x", headers=a).status_code != 200
