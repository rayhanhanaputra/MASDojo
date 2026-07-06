"""Seeded challenge generator for 051 — Cleartext traffic leak.

A capture of several requests. Most go over HTTPS; one — the login — goes over
plain HTTP, and its credential is base64-encoded in the body. The learner must
spot the cleartext (http://) request among the TLS ones (that's the vulnerability)
and decode the credential. The plaintext credential never appears in the capture.
Seeded per learner.
"""

from __future__ import annotations

import base64
import random
from typing import Any


def generate(seed: str) -> dict[str, Any]:
    rng = random.Random(seed)
    user = rng.choice(["alice", "bob", "carol", "dave", "erin"])
    cred = "cred_" + "".join(rng.choice("0123456789abcdef") for _ in range(20))
    b64 = base64.b64encode(cred.encode()).decode()

    reqs = [
        "GET https://api.vaultbank.example/v1/config HTTP/1.1\n"
        "Host: api.vaultbank.example\n(TLS — encrypted)\n",
        # the vulnerability: login over plain HTTP, credential base64 in the body
        "POST http://api.vaultbank.example/v1/login HTTP/1.1\n"
        "Host: api.vaultbank.example\n"
        "Content-Type: application/json\n\n"
        f'{{"user":"{user}","password":"{b64}"}}\n',
        "GET https://api.vaultbank.example/v1/balance HTTP/1.1\n"
        "Host: api.vaultbank.example\n(TLS — encrypted)\n",
    ]
    rng.shuffle(reqs)
    capture = "\n----\n".join(reqs)
    return {"answer": cred, "files": {"capture.txt": capture}}
