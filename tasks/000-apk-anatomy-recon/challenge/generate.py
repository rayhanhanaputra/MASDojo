"""Seeded challenge generator for 000 — APK anatomy & recon.

The decoded resources (as from `apktool d`) hide a leftover debug secret among
ordinary strings — but base64-encoded, the way devs "hide" notes in resources.
The learner must browse the resources, spot the odd encoded string, and decode
it. The plaintext flag never appears in the files. Seeded per learner.
"""

from __future__ import annotations

import base64
import random
from typing import Any


def generate(seed: str) -> dict[str, Any]:
    rng = random.Random(seed)
    flag = "FLAG{4pk_r3con_c0mpl3t3_" + "".join(rng.choice("0123456789abcdef") for _ in range(6)) + "}"
    b64 = base64.b64encode(flag.encode()).decode()

    manifest = (
        '<?xml version="1.0" encoding="utf-8"?>\n'
        "<!-- Decoded AndroidManifest.xml from `apktool d recon.apk`. -->\n"
        '<manifest package="org.masdojo.recon">\n'
        '    <uses-permission android:name="android.permission.INTERNET" />\n'
        '    <uses-permission android:name="android.permission.READ_CONTACTS" />\n'
        '    <application android:debuggable="true" android:allowBackup="true">\n'
        '        <activity android:name=".MainActivity" android:exported="true"/>\n'
        '        <activity android:name=".DebugActivity" android:exported="true"/>\n'
        "    </application>\n"
        "</manifest>\n"
    )
    strings = (
        '<?xml version="1.0" encoding="utf-8"?>\n'
        "<!-- res/values/strings.xml — devs leave notes/secrets here thinking\n"
        "     nobody decodes the APK. Not all of these are what they look like. -->\n"
        "<resources>\n"
        '    <string name="app_name">Recon</string>\n'
        '    <string name="welcome_body">Your account is being set up.</string>\n'
        '    <string name="build_channel">internal-qa</string>\n'
        '    <string name="support_email">support@recon.example</string>\n'
        f'    <string name="qa_unlock_note">{b64}</string>\n'
        '    <string name="privacy_url">https://recon.example/privacy</string>\n'
        "</resources>\n"
    )
    return {
        "answer": flag,
        "files": {
            "AndroidManifest.xml": manifest,
            "res/values/strings.xml": strings,
        },
    }
