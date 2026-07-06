"""Seeded challenge generator for 083 — Leaky content provider.

The learner gets the decompiled provider, which stores its secret row
base64-encoded (so a raw `content query` dump shows an opaque blob, not the
flag). The learner must recognise the exported provider, and base64-decode the
value it returns. Seeded per learner.
"""

from __future__ import annotations

import base64
import random
from typing import Any


def generate(seed: str) -> dict[str, Any]:
    rng = random.Random(seed)
    flag = "FLAG{c0nt3nt_pr0v1d3r_l34k_" + "".join(rng.choice("0123456789abcdef") for _ in range(6)) + "}"
    b64 = base64.b64encode(flag.encode()).decode()

    code = (
        "// Decompiled — com.vaultbank.provider.VaultProvider\n"
        "// AndroidManifest: <provider android:name=\".VaultProvider\"\n"
        "//   android:authorities=\"com.vaultbank.provider\" android:exported=\"true\"/>\n"
        "// -> any app can:  adb shell content query --uri content://com.vaultbank.provider/secrets\n"
        "public class VaultProvider extends ContentProvider {\n"
        "    public Cursor query(...) {\n"
        "        MatrixCursor c = new MatrixCursor(new String[]{\"_id\", \"name\", \"value\"});\n"
        "        // values are stored base64-encoded (not encrypted)\n"
        f'        c.addRow(new Object[]{{1, "api_secret", "{b64}"}});\n'
        "        return c;\n"
        "    }\n"
        "}\n"
    )
    dump = (
        "$ adb shell content query --uri content://com.vaultbank.provider/secrets\n"
        f"Row: 0 _id=1, name=api_secret, value={b64}\n"
    )
    return {
        "answer": flag,
        "files": {
            "decompiled/VaultProvider.java": code,
            "provider_dump.txt": dump,
        },
    }
