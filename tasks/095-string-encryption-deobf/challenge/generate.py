"""Seeded challenge generator for 095 — Defeat string encryption.

The learner gets the decompiled `StringVault` decode routine and an encrypted
string table. The reward entry is XOR-encrypted with a key that also ships in the
binary, so it can't be lifted from a `strings` dump — but it isn't a secret
either: replaying the XOR reconstructs it. Decoy entries make it a real table.
Seeded per learner so a recovered value can't be shared.
"""

from __future__ import annotations

import random
from typing import Any


def _xor_hex(s: str, key: int) -> str:
    return "".join(f"{b ^ key:02x}" for b in s.encode())


def generate(seed: str) -> dict[str, Any]:
    rng = random.Random(seed)
    flag = "FLAG{str1ng_3ncrypt10n_1s_n0t_4_c0ntr0l_" + \
        "".join(rng.choice("0123456789abcdef") for _ in range(6)) + "}"
    key = rng.randint(1, 255)

    # A small string table: two decoys plus the reward, all XOR'd with the same key.
    decoys = {
        "telemetry_host": "telemetry.vaultbank.example",
        "build_channel": "internal-canary",
    }
    entries = {name: _xor_hex(val, key) for name, val in decoys.items()}
    entries["reward"] = _xor_hex(flag, key)
    # Present the table in a stable, shuffled-but-deterministic order.
    ordered = list(entries.items())
    rng.shuffle(ordered)
    table_src = "\n".join(f'        "{k}" -> "{v}",' for k, v in ordered)

    smali_like = (
        "// Decompiled — org.masdojo.vaultbank.StringVault  (RASP: anti-static-analysis)\n"
        "// Constants are XOR-encrypted so they don't appear in a `strings` dump.\n"
        "// The key ships right next to the ciphertext, so this only slows analysis.\n\n"
        "public final class StringVault {\n\n"
        f"    private static final int XOR_KEY = 0x{key:02x};\n\n"
        "    // name -> ciphertext (hex).  Want the 'reward' entry's plaintext.\n"
        "    private static final Map<String,String> TABLE = mapOf(\n"
        f"{table_src}\n"
        "    );\n\n"
        "    // Runtime decode: hex-decode, then XOR every byte with XOR_KEY.\n"
        "    public static String decode(String name) {\n"
        "        byte[] b = hexToBytes(TABLE.get(name));\n"
        "        for (int i = 0; i < b.length; i++) b[i] ^= XOR_KEY;\n"
        "        return new String(b);\n"
        "    }\n"
        "}\n"
    )
    return {
        "answer": flag,
        "files": {"decompiled/StringVault.java": smali_like},
    }
