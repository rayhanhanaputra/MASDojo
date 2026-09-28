"""Seeded challenge generator for 084 — Confused-deputy privilege re-delegation.

The learner gets the manifest entry (proving the receiver is exported with NO
permission and no caller check) and the decompiled receiver. Its onReceive()
performs a PRIVILEGED action — minting an elevation grant — for whoever sends the
intent: a userland confused deputy. The grant token is XOR-obfuscated in code, so
the learner must (1) realise a low-privileged caller can trigger the action and
(2) reconstruct the grant it returns. Seeded per learner.
"""

from __future__ import annotations

import random
from typing import Any


def _xor_hex(s: str, key: int) -> str:
    return "".join(f"{b ^ key:02x}" for b in s.encode())


def generate(seed: str) -> dict[str, Any]:
    rng = random.Random(seed)
    grant = "FLAG{c0nfus3d_d3puty_" + \
        "".join(rng.choice("0123456789abcdef") for _ in range(6)) + "}"
    key = rng.randint(1, 255)
    enc = _xor_hex(grant, key)

    manifest = (
        "<!-- AndroidManifest.xml (excerpt) -->\n"
        "<!-- Exported, NO android:permission, no signature guard: any caller can send this. -->\n"
        '<receiver android:name=".GrantReceiver" android:exported="true">\n'
        "    <intent-filter>\n"
        '        <action android:name="org.masdojo.vaultbank.action.ELEVATE"/>\n'
        "    </intent-filter>\n"
        "</receiver>\n"
    )
    receiver = (
        "// Decompiled — org.masdojo.vaultbank.GrantReceiver\n"
        "// Reachable by a low-privileged caller:\n"
        "//   adb shell am broadcast -a org.masdojo.vaultbank.action.ELEVATE \\\n"
        "//     --es requester attacker org.masdojo.vaultbank\n"
        "// It performs a PRIVILEGED action for ANY caller — a confused deputy.\n"
        "public class GrantReceiver extends BroadcastReceiver {\n"
        f'    private static final String ENC = "{enc}";\n'
        f"    private static final int GRANT_KEY = 0x{key:02x};\n\n"
        "    public void onReceive(Context ctx, Intent intent) {\n"
        '        if (!intent.getAction().equals("org.masdojo.vaultbank.action.ELEVATE")) return;\n'
        "        // NO caller check, NO permission: whoever asks gets elevated.\n"
        "        String grant = decodeGrant();   // hex-decode ENC, XOR each byte with GRANT_KEY\n"
        "        setResultData(grant);           // handed straight back to the caller\n"
        '        Log.i("VaultBank", "MASDOJO_UNLOCK:" + grant);\n'
        "    }\n\n"
        "    private String decodeGrant() {\n"
        "        byte[] b = hexToBytes(ENC);\n"
        "        for (int i = 0; i < b.length; i++) b[i] ^= GRANT_KEY;\n"
        "        return new String(b);\n"
        "    }\n"
        "}\n"
    )
    return {
        "answer": grant,
        "files": {
            "AndroidManifest.xml": manifest,
            "decompiled/GrantReceiver.java": receiver,
        },
    }
