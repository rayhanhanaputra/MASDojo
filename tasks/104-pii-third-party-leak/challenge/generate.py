"""Seeded challenge generator for 104 — PII leaked to a third-party SDK.

Each learner's captured analytics request carries a *different* user email being
exfiltrated to a third-party tracker, so a value shared by one learner is useless
to another. The runner regenerates the same email from the learner's seed to
grade. Never shipped to the client — only the generated capture is served; the
learner must read the request and spot the PII that shouldn't leave the device.
"""

from __future__ import annotations

import random
from typing import Any


def generate(seed: str) -> dict[str, Any]:
    rng = random.Random(seed)
    name = rng.choice(["alex", "jordan", "sam", "taylor", "riley", "casey", "morgan"])
    email = f"{name}{rng.randint(100, 9999)}@gmail.com"
    hexid = "".join(rng.choice("0123456789abcdef") for _ in range(16))
    adid = f"{hexid[:8]}-{hexid[8:12]}-{hexid[12:16]}"

    body = (
        '{"event":"app_open",'
        f'"advertising_id":"{adid}",'
        f'"user_email":"{email}",'
        '"device":"Pixel 6","locale":"en_US","app":"org.masdojo.vaultbank"}'
    )
    capture = (
        "POST /collect HTTP/1.1\r\n"
        "Host: in.thirdparty-metrics.example\r\n"
        "Content-Type: application/json\r\n"
        "User-Agent: VaultBank/1.0 (analytics-sdk 4.2.1)\r\n"
        f"Content-Length: {len(body)}\r\n"
        "\r\n"
        f"{body}\n"
    )
    return {
        "answer": email,
        "files": {"capture.txt": capture},
        "present_in": ["capture.txt"],
    }
