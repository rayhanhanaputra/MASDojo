"""Proof-of-Pwn certificates: tamper-evident, server-verifiable PASS receipts.

When a submission PASSes, the server issues a compact signed token binding the
verdict to the task, the learner, the score, and a digest of the grading
evidence. Anyone can POST the token to the public /verify endpoint to confirm
*this server* issued it (untampered) and read its claims — a tamper-evident
receipt, not a self-justified one.

Scope (be honest about what it proves): this is HMAC-SHA256 keyed from the
server's MASTER_KEY, so it proves a holder of that key issued the token and the
claims weren't altered. It is NOT third-party-verifiable without the server, and
it does not by itself prove the server graded honestly — its integrity is only
as strong as MASTER_KEY (which the startup guard refuses to leave at its default).
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
from typing import Any

from app.core.config import settings

CERT_VERSION = 1


def _key() -> bytes:
    return hashlib.sha256(("masdojo-proof:" + settings.master_key).encode()).digest()


def _b64(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).decode().rstrip("=")


def _unb64(s: str) -> bytes:
    return base64.urlsafe_b64decode(s + "=" * (-len(s) % 4))


def evidence_digest(evidence: str, checks: list[dict[str, Any]]) -> str:
    """Stable SHA-256 over the grading evidence + per-check results."""
    blob = json.dumps({"evidence": evidence, "checks": checks}, sort_keys=True).encode()
    return hashlib.sha256(blob).hexdigest()


def issue_certificate(payload: dict[str, Any]) -> str:
    """Return a compact `<body>.<sig>` token for the given claims."""
    body = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    sig = hmac.new(_key(), body, hashlib.sha256).digest()
    return f"{_b64(body)}.{_b64(sig)}"


def verify_certificate(token: str) -> dict[str, Any] | None:
    """Return the verified claims, or None if the token is invalid/tampered."""
    try:
        body_b64, sig_b64 = token.strip().split(".")
        body = _unb64(body_b64)
        sig = _unb64(sig_b64)
    except Exception:  # noqa: BLE001 - any malformed token -> invalid
        return None
    expected = hmac.new(_key(), body, hashlib.sha256).digest()
    if not hmac.compare_digest(expected, sig):
        return None
    try:
        return json.loads(body)
    except json.JSONDecodeError:
        return None
