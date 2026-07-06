"""Seeded challenge generator for 092 — Defeat the integrity/tamper check.

The learner gets the decompiled integrity check. The reward string on the
"valid" branch is XOR-obfuscated, so it can't be lifted straight from the smali:
the learner must understand that flipping the tamper check reaches the valid
branch, and reconstruct the obfuscated value it returns. Seeded per learner.
"""

from __future__ import annotations

import random
from typing import Any


def _xor_hex(s: str, key: int) -> str:
    return "".join(f"{b ^ key:02x}" for b in s.encode())


def generate(seed: str) -> dict[str, Any]:
    rng = random.Random(seed)
    flag = "FLAG{1nt3grity_byp4ss3d_" + "".join(rng.choice("0123456789abcdef") for _ in range(6)) + "}"
    key = rng.randint(1, 255)
    enc = _xor_hex(flag, key)

    smali = (
        ".class public Lcom/vaultbank/IntegrityCheck;\n"
        ".super Ljava/lang/Object;\n\n"
        "# verify(): if the signature doesn't match the official one, bail to :tampered.\n"
        "# The reward on the valid path is XOR-obfuscated (decoded before return).\n"
        f'.field private static final ENC:Ljava/lang/String; = "{enc}"\n'
        f".field private static final XOR_KEY:I = 0x{key:02x}\n\n"
        ".method public verify()Ljava/lang/String;\n"
        "    .registers 4\n"
        "    invoke-static {}, Lcom/vaultbank/Sig;->matchesOfficial()Z\n"
        "    move-result v0\n"
        "    if-eqz v0, :tampered           # <-- flip/patch this branch to reach the valid path\n"
        "    # valid path: decode ENC with XOR_KEY and return it\n"
        "    invoke-static {}, Lcom/vaultbank/IntegrityCheck;->decodeReward()Ljava/lang/String;\n"
        "    move-result-object v1\n"
        "    return-object v1\n"
        "    :tampered\n"
        '    const-string v1, "Tampered — refusing to run"\n'
        "    return-object v1\n"
        ".end method\n"
    )
    return {"answer": flag, "files": {"smali/IntegrityCheck.smali": smali}}
