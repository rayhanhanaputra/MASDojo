"""Seeded challenge generator for 023 — adb backup extraction.

The learner is handed the actual backup archive (a gzip'd tar, base64-wrapped so
it can be served as text), NOT a pre-extracted file. To read the notes they must
unpack it — base64-decode, gunzip, untar — which is the whole point of the task
(extracting an `adb backup`). The recovery key is inside `notes.txt`. Seeded.
"""

from __future__ import annotations

import base64
import gzip
import io
import random
import tarfile
from typing import Any

_REL = "backup.tar.gz.b64"


def generate(seed: str) -> dict[str, Any]:
    rng = random.Random(seed)
    key = "rec_" + "".join(rng.choice("0123456789abcdef") for _ in range(24))
    chore = rng.choice(["buy milk", "call the bank", "renew passport", "water plants"])
    notes = f"note#1: {chore}\nnote#2: recovery phrase -> {key}\n".encode()

    # Build a deterministic tar (mtime fixed) -> gzip -> base64 text.
    tar_buf = io.BytesIO()
    with tarfile.open(fileobj=tar_buf, mode="w") as tar:
        info = tarfile.TarInfo(name="apps/org.masdojo.notes/db/notes.txt")
        info.size = len(notes)
        info.mtime = 0
        tar.addfile(info, io.BytesIO(notes))
    gz = gzip.compress(tar_buf.getvalue(), mtime=0)
    blob = base64.b64encode(gz).decode()
    # wrap to 76-char lines like a real base64 dump
    wrapped = "\n".join(blob[i : i + 76] for i in range(0, len(blob), 76)) + "\n"

    return {"answer": key, "files": {_REL: wrapped}}
