"""Seeded challenge generator for 023 — adb Backup Extraction.

Each learner's extracted backup contains a *different* recovery key, so answers
can't be shared. The runner regenerates the same key from the learner's seed to
grade. Never shipped to the client — only the generated notes file is served.
"""

from __future__ import annotations

import random
from typing import Any

_REL = "backup/org.masdojo.notes/db/notes.txt"


def generate(seed: str) -> dict[str, Any]:
    rng = random.Random(seed)
    key = "rec_" + "".join(rng.choice("0123456789abcdef") for _ in range(24))
    chore = rng.choice(["buy milk", "call the bank", "renew passport", "water plants"])
    notes = f"note#1: {chore}\nnote#2: recovery phrase -> {key}\n"
    return {"answer": key, "files": {_REL: notes}, "present_in": [_REL]}
