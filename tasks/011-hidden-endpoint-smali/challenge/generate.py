"""Seeded challenge generator for 011 — Hidden endpoint in smali.

The admin path is not a plain `const-string` — it is XOR-obfuscated and rebuilt
at runtime (a common trick to keep URLs out of `strings`/grep). The learner must
read the smali, take the encoded bytes and the key, and reconstruct the path.
Seeded per learner. The decoded path never appears verbatim in the file.
"""

from __future__ import annotations

import random
from typing import Any

_REL = "smali/com/vaultbank/net/DebugApi.smali"


def _xor_hex(s: str, key: int) -> str:
    return "".join(f"{b ^ key:02x}" for b in s.encode())


def generate(seed: str) -> dict[str, Any]:
    rng = random.Random(seed)
    path = "/internal/v1/admin/" + "".join(rng.choice("0123456789abcdef") for _ in range(8))
    key = rng.randint(1, 255)
    enc = _xor_hex(path, key)

    smali = (
        ".class public Lcom/vaultbank/net/DebugApi;\n"
        ".super Ljava/lang/Object;\n\n"
        "# The admin route is XOR-obfuscated at build time and rebuilt before use,\n"
        "# so it does not show up as a plain URL string in the binary.\n"
        f'.field private static final ENC:Ljava/lang/String; = "{enc}"\n'
        f".field private static final XOR_KEY:I = 0x{key:02x}\n\n"
        ".method public static adminUrl()Ljava/lang/String;\n"
        "    .registers 4\n"
        "    # loads ENC (hex), decodes each byte as (b ^ XOR_KEY), returns the path\n"
        "    invoke-static {}, Lcom/vaultbank/net/DebugApi;->decodeHex(ENC)[B\n"
        "    # ... for-loop: aput-byte (xor v, XOR_KEY) ...\n"
        "    new-instance v0, Ljava/lang/String;\n"
        "    invoke-direct {v0, v1}, Ljava/lang/String;-><init>([B)V\n"
        "    return-object v0\n"
        ".end method\n"
    )
    return {"answer": path, "files": {_REL: smali}}
