"""Seeded challenge generator for 022 — Sensitive Data in Logs.

Each learner gets a logcat dump leaking a *different* session token, so a token
shared by one learner is worthless to another. The runner regenerates the same
token from the learner's seed to grade. Never shipped to the client — only the
generated `logcat.txt` is served.
"""

from __future__ import annotations

import random
from typing import Any


def generate(seed: str) -> dict[str, Any]:
    rng = random.Random(seed)
    token = "sess_" + "".join(rng.choice("0123456789abcdef") for _ in range(20))
    user = rng.choice(["alice", "bob", "carol", "dave", "erin"])
    log = (
        "I/Activity: onCreate\n"
        "D/Net: GET /api/profile 200\n"
        f"D/AuthManager: issuing session for {user} token={token}\n"
        "I/Activity: onResume\n"
        "W/Net: retry 1\n"
    )
    return {"answer": token, "files": {"logcat.txt": log}, "present_in": ["logcat.txt"]}
