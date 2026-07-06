"""Seeded challenge generator for 081 — Exported activity / deep-link abuse.

The learner gets the manifest entry (proving the activity is exported with a
deep link) and the decompiled activity. The flag the activity reveals is
XOR-obfuscated in code, so it can't be read straight off — the learner must
understand that the screen is reachable without auth AND reconstruct the value.
Seeded per learner.
"""

from __future__ import annotations

import random
from typing import Any


def _xor_hex(s: str, key: int) -> str:
    return "".join(f"{b ^ key:02x}" for b in s.encode())


def generate(seed: str) -> dict[str, Any]:
    rng = random.Random(seed)
    flag = "FLAG{exp0rt3d_r34ch3d_" + "".join(rng.choice("0123456789abcdef") for _ in range(6)) + "}"
    key = rng.randint(1, 255)
    enc = _xor_hex(flag, key)

    manifest = (
        '<!-- AndroidManifest.xml (excerpt) -->\n'
        '<activity android:name=".SecretActivity" android:exported="true">\n'
        '    <intent-filter>\n'
        '        <action android:name="android.intent.action.VIEW"/>\n'
        '        <category android:name="android.intent.category.BROWSABLE"/>\n'
        '        <data android:scheme="vaultbank" android:host="secret"/>\n'
        '    </intent-filter>\n'
        '</activity>\n'
    )
    activity = (
        "// Decompiled — com.vaultbank.SecretActivity\n"
        "public class SecretActivity extends Activity {\n"
        "    // reachable via:  adb shell am start -a android.intent.action.VIEW -d \"vaultbank://secret\"\n"
        "    // no caller/permission check — any app or the shell can open it.\n"
        f'    private static final String ENC = "{enc}";\n'
        f"    private static final int XOR_KEY = 0x{key:02x};\n"
        "    void onCreate(Bundle b) {\n"
        "        byte[] d = hexToBytes(ENC);\n"
        "        for (int i = 0; i < d.length; i++) d[i] ^= XOR_KEY;\n"
        "        show(new String(d));   // renders the flag on screen\n"
        "    }\n"
        "}\n"
    )
    return {
        "answer": flag,
        "files": {
            "AndroidManifest.xml": manifest,
            "decompiled/SecretActivity.java": activity,
        },
    }
