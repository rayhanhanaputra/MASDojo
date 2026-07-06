"""Seeded challenge generator for 021 — Secrets in SharedPreferences.

The app caches a session token in shared_prefs — but stored **base64-encoded**,
as many apps do (base64 is not encryption). The learner must recognise the
encoded value in the XML and decode it; the plaintext token never appears in the
file. Seeded per learner so a decoded token can't be shared.
"""

from __future__ import annotations

import base64
import random
from typing import Any


def generate(seed: str) -> dict[str, Any]:
    rng = random.Random(seed)
    token = "sk_live_" + "".join(rng.choice("0123456789abcdef") for _ in range(32))
    b64 = base64.b64encode(token.encode()).decode()
    user_id = 10000 + rng.randint(0, 89999)

    xml = (
        "<?xml version='1.0' encoding='utf-8' standalone='yes' ?>\n"
        "<map>\n"
        f'    <int name="user_id" value="{user_id}" />\n'
        '    <boolean name="onboarded" value="true" />\n'
        '    <string name="theme">dark</string>\n'
        "    <!-- token cached for 'convenience' — base64, not encrypted -->\n"
        f'    <string name="auth_token">{b64}</string>\n'
        "</map>\n"
    )
    return {"answer": token, "files": {"shared_prefs/auth.xml": xml}}
