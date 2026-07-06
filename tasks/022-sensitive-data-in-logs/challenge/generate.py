"""Seeded challenge generator for 022 — Sensitive data in logs.

A realistic, noisy logcat dump. One line leaks an HTTP `Authorization: Basic`
header — base64 of `user:<token>`. The learner must filter the noise to find it
and base64-decode it to recover the token. The plaintext token never appears in
the log. Seeded per learner.
"""

from __future__ import annotations

import base64
import random
from typing import Any

_NOISE = [
    "I/Choreographer: Skipped 31 frames! The application may be doing too much work on its main thread.",
    "D/EGL_emulation: eglMakeCurrent: 0x... ver 3 0 (tinfo 0x...)",
    "I/Activity: onResume",
    "D/Net: GET /api/profile 200 (142ms)",
    "W/OkHttpClient: A connection to https://api.vaultbank.example was leaked.",
    "I/zygote: Do partial code cache collection, code=30KB, data=25KB",
    "D/Net: GET /api/accounts 200 (88ms)",
    "V/FA: Inactivity, disconnecting from the service",
    "I/Activity: onPause",
    "D/EGL_emulation: eglCreateContext: 0x...",
]


def generate(seed: str) -> dict[str, Any]:
    rng = random.Random(seed)
    token = "tok_" + "".join(rng.choice("0123456789abcdef") for _ in range(24))
    user = rng.choice(["alice", "bob", "carol", "dave", "erin"])
    basic = base64.b64encode(f"{user}:{token}".encode()).decode()

    lines = list(_NOISE)
    # drop the leaking line somewhere in the middle of the noise
    leak = f"D/OkHttp: --> Authorization: Basic {basic}"
    lines.insert(rng.randint(3, len(lines) - 2), leak)
    # a couple more noise lines shuffled in
    rng.shuffle(lines)
    log = "\n".join(lines) + "\n"
    return {"answer": token, "files": {"logcat.txt": log}}
