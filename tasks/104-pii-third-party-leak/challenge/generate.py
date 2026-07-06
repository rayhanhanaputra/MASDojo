"""Seeded challenge generator for 104 — PII leaked to a third-party SDK.

The learner gets a capture of SEVERAL startup requests: the app's own first-party
API (benign), plus third-party SDKs (ads/metrics). Only one — a third-party
tracker — exfiltrates the user's email, and it's base64-encoded in the body. The
learner must (a) tell first-party from third-party hosts, (b) spot the PII field,
(c) decode it. The plaintext email never appears in the capture. Seeded.
"""

from __future__ import annotations

import base64
import random
from typing import Any


def _req(host: str, path: str, body: str) -> str:
    return (
        f"POST {path} HTTP/1.1\r\n"
        f"Host: {host}\r\n"
        "Content-Type: application/json\r\n"
        f"Content-Length: {len(body)}\r\n"
        "\r\n"
        f"{body}"
    )


def generate(seed: str) -> dict[str, Any]:
    rng = random.Random(seed)
    name = rng.choice(["alex", "jordan", "sam", "taylor", "riley", "casey", "morgan"])
    email = f"{name}{rng.randint(100, 9999)}@gmail.com"
    hexid = "".join(rng.choice("0123456789abcdef") for _ in range(16))

    requests = [
        # first-party — the app's own backend, no PII (device counters only)
        _req("api.vaultbank.example", "/v1/metrics",
             '{"session_len":42,"screen":"dashboard","build":"1.4.0"}'),
        # third-party analytics SDK — leaks the user's email (base64), the violation
        _req("in.thirdparty-metrics.example", "/collect",
             '{"event":"app_open","aid":"' + hexid[:8] + '","u":"'
             + base64.b64encode(email.encode()).decode() + '"}'),
        # third-party ad SDK — benign device signal, decoy
        _req("ads.partner-network.example", "/rtb",
             '{"ifa":"' + hexid[8:] + '","w":1080,"h":2400,"os":"android"}'),
    ]
    rng.shuffle(requests)
    capture = "\n\n".join(requests) + "\n"
    return {"answer": email, "files": {"traffic.txt": capture}}
