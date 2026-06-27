"""Symmetric encryption for BYOK API keys at rest.

Per-user provider keys are encrypted with Fernet, keyed by the server's
MASTER_KEY. Ciphertext is what we persist; plaintext only ever lives in memory
for the duration of an AI call. Keys are never logged and never returned to the
client after entry.
"""

from __future__ import annotations

import base64
import hashlib

from cryptography.fernet import Fernet, InvalidToken

from app.core.config import settings


def _derive_fernet_key(master_key: str) -> bytes:
    """Accept either a raw Fernet key or any string, deriving a valid 32-byte key.

    If MASTER_KEY is already a urlsafe-base64 32-byte Fernet key we use it
    directly; otherwise we derive one deterministically via SHA-256 so operators
    can set any sufficiently-random secret.
    """
    raw = master_key.encode()
    try:
        if len(base64.urlsafe_b64decode(raw)) == 32:
            return raw
    except (ValueError, Exception):  # noqa: BLE001 - any decode failure -> derive
        pass
    digest = hashlib.sha256(raw).digest()
    return base64.urlsafe_b64encode(digest)


_fernet = Fernet(_derive_fernet_key(settings.master_key))


def encrypt_secret(plaintext: str) -> str:
    """Encrypt a secret, returning urlsafe base64 ciphertext (str)."""
    return _fernet.encrypt(plaintext.encode()).decode()


def decrypt_secret(ciphertext: str) -> str:
    """Decrypt ciphertext produced by `encrypt_secret`.

    Raises `ValueError` if the token is invalid (e.g. master key changed).
    """
    try:
        return _fernet.decrypt(ciphertext.encode()).decode()
    except InvalidToken as exc:  # pragma: no cover - defensive
        raise ValueError("could not decrypt stored secret") from exc


def mask_key(plaintext: str) -> str:
    """Produce a display-safe masked form, e.g. 'sk-…abcd'."""
    if len(plaintext) <= 6:
        return "…" + plaintext[-2:]
    prefix = plaintext[:3]
    return f"{prefix}…{plaintext[-4:]}"
