"""Seeded challenge generator for 011 — Hidden Endpoint in smali.

Each learner's decompiled smali embeds a *different* admin endpoint path, so a
path shared by one learner won't solve another's. The runner regenerates the
same path from the learner's seed to grade. Never shipped to the client — only
the generated smali is served.
"""

from __future__ import annotations

import random
from typing import Any

_REL = "smali/DebugApi.smali"


def generate(seed: str) -> dict[str, Any]:
    rng = random.Random(seed)
    path = "/internal/v1/admin/" + "".join(rng.choice("0123456789abcdef") for _ in range(8))
    smali = (
        ".class public Lorg/masdojo/app/DebugApi;\n"
        ".super Ljava/lang/Object;\n\n"
        ".method public static adminUrl()Ljava/lang/String;\n"
        "    .registers 1\n"
        f'    const-string v0, "{path}"\n'
        "    return-object v0\n"
        ".end method\n"
    )
    return {"answer": path, "files": {_REL: smali}, "present_in": [_REL]}
