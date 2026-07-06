"""VaultBank API — an intentionally-vulnerable REST backend for Lab 3.

This is the *live* target for the API-abuse module: learners exploit it directly
(curl / Burp / mitmproxy) to recover the flags, then submit them to MASDojo,
which grades by value. It holds no real data.

Vulnerabilities:
  - IDOR (MASVS-AUTHZ, task 071): GET /orders/{id} authenticates the caller but
    never checks they own the order, so incrementing the id reads another user's
    record — order 1337 belongs to someone else and carries the flag.
  - Broken auth / JWT alg:none (MASVS-AUTH, task 072): the token verifier trusts
    the header `alg`. A forged, unsigned `{"alg":"none"}` token with role=admin
    is accepted, unlocking /admin/ledger.

The flags match each task's grader/expected.json, so a learner who exploits the
live API recovers exactly the value the grader expects.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
from typing import Any

from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel

# The HS256 signing secret (a real server would keep this out of reach; here the
# point is that the alg:none path skips signature checks entirely).
_SECRET = b"vaultbank-jwt-signing-secret"

IDOR_FLAG = "FLAG{id0r_cr0ss_us3r}"
JWT_FLAG = "FLAG{jwt_n0n3_f0rg3d}"

# Seeded so the learner's own orders are mundane and #1337 (another user's) holds
# the flag — only reachable by tampering with the id.
ORDERS: dict[int, dict[str, Any]] = {
    1001: {"id": 1001, "owner": "u1001", "item": "Coffee mug", "total": "12.00", "note": "thanks!"},
    1002: {"id": 1002, "owner": "u1001", "item": "Notebook", "total": "8.50", "note": "gift wrap"},
    1337: {"id": 1337, "owner": "ceo", "item": "Wire transfer", "total": "250000.00", "note": IDOR_FLAG},
}


def _b64u(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).decode().rstrip("=")


def _unb64u(s: str) -> bytes:
    return base64.urlsafe_b64decode(s + "=" * (-len(s) % 4))


def make_jwt(payload: dict[str, Any]) -> str:
    header = {"alg": "HS256", "typ": "JWT"}
    h = _b64u(json.dumps(header).encode())
    p = _b64u(json.dumps(payload).encode())
    sig = _b64u(hmac.new(_SECRET, f"{h}.{p}".encode(), hashlib.sha256).digest())
    return f"{h}.{p}.{sig}"


def decode_jwt(token: str) -> dict[str, Any]:
    """VULNERABILITY (task 072): trusts the header `alg`. When it is `none` the
    payload is accepted with no signature — the classic alg-confusion forge."""
    try:
        h_b64, p_b64, sig_b64 = token.split(".")
        header = json.loads(_unb64u(h_b64))
        payload = json.loads(_unb64u(p_b64))
    except Exception:
        raise HTTPException(401, "malformed token")

    if str(header.get("alg", "")).lower() == "none":
        return payload  # <-- no signature required

    expected = _b64u(hmac.new(_SECRET, f"{h_b64}.{p_b64}".encode(), hashlib.sha256).digest())
    if not hmac.compare_digest(expected, sig_b64):
        raise HTTPException(401, "bad signature")
    return payload


def _claims(authorization: str | None) -> dict[str, Any]:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(401, "missing bearer token")
    return decode_jwt(authorization.split(" ", 1)[1])


app = FastAPI(title="VaultBank API (intentionally vulnerable)")


class Login(BaseModel):
    username: str = "demo"
    password: str = "demo"


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/login")
def login(body: Login) -> dict[str, str]:
    # Any credentials mint a normal-user token (role=user). Escalating to admin
    # is the learner's job (task 072).
    return {"access_token": make_jwt({"sub": "u1001", "role": "user"}), "token_type": "bearer"}


@app.get("/orders/{order_id}")
def get_order(order_id: int, authorization: str | None = Header(None)) -> dict[str, Any]:
    _claims(authorization)  # authenticated…
    order = ORDERS.get(order_id)
    if not order:
        raise HTTPException(404, "no such order")
    # VULNERABILITY (IDOR, task 071): no check that the caller owns this order.
    return order


@app.get("/admin/ledger")
def admin_ledger(authorization: str | None = Header(None)) -> dict[str, Any]:
    claims = _claims(authorization)
    if claims.get("role") != "admin":
        raise HTTPException(403, "admin role required")
    # Reached only by forging an alg:none token with role=admin (task 072).
    return {"ledger": "internal", "flag": JWT_FLAG}
