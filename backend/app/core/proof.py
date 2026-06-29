"""Proof-of-Pwn certificates: tamper-evident, verifiable PASS receipts.

When a submission PASSes, the server issues a compact signed token binding the
verdict to the task, the learner, the score, and a digest of the grading
evidence. Anyone can POST the token to the public /verify endpoint to confirm it
was genuinely issued by this server and read its claims — answering the security
audience's first question about any auto-grader: "how do I know that PASS isn't
faked?".

Signed with HMAC-SHA256 keyed from the server's MASTER_KEY (the same secret that
protects BYOK keys). Symmetric is sufficient because verification is done by the
server's own /verify endpoint.
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
    except (ValueError, Exception):  # noqa: BLE001 - any malformed token -> invalid
        return None
    expected = hmac.new(_key(), body, hashlib.sha256).digest()
    if not hmac.compare_digest(expected, sig):
        return None
    try:
        return json.loads(body)
    except json.JSONDecodeError:
        return None
