"""Seeded challenge generator for 021 — Secrets in SharedPreferences.

Each learner gets their own SharedPreferences dump with a *different* auth token
embedded in the clear. The token is derived deterministically from the learner's
seed, so:

  - the same learner always sees the same file (they can revisit), and
  - a token shared by one learner is worthless to another (different answer), and
  - the runner regenerates the identical token from the same seed to grade.

The token is 32 hex chars of entropy — unguessable — so a correct submission is
itself proof the learner read it out of their own artifact.

Never shipped to the client (only artifacts/ is served): the learner receives
`shared_prefs/auth.xml` and must extract the token from it.
"""

from __future__ import annotations

import random
from typing import Any


def generate(seed: str) -> dict[str, Any]:
    rng = random.Random(seed)
    token = "sk_live_" + "".join(rng.choice("0123456789abcdef") for _ in range(32))
    user_id = 10000 + rng.randint(0, 89999)
    session = "".join(rng.choice("0123456789abcdef") for _ in range(16))

    xml = (
        "<?xml version='1.0' encoding='utf-8' standalone='yes' ?>\n"
        "<map>\n"
        f'    <int name="user_id" value="{user_id}" />\n'
        '    <boolean name="onboarded" value="true" />\n'
        f'    <string name="auth_token">{token}</string>\n'
        f'    <string name="session_id">{session}</string>\n'
        '    <string name="theme">dark</string>\n'
        "</map>\n"
    )

    return {
        "answer": token,
        "files": {"shared_prefs/auth.xml": xml},
        # Anti-guess: the exact token must appear in the served file.
        "present_in": ["shared_prefs/auth.xml"],
    }
