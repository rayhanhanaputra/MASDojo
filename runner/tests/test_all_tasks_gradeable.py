"""Every implemented task must detect a correct submission (PASS) and reject a
wrong one (FAIL) in dry-run — the payload-detection system, exercised end to end
across the whole curriculum. Also verifies the crypto tasks' committed
ciphertext genuinely decrypts to the expected flag (so they're really solvable).
"""

from __future__ import annotations

import base64
import json
from pathlib import Path

import pytest
import yaml
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

from runner.grade_runner import GradeRunner
from runner.seeds import generate_challenge

# A fixed seed for grading seeded tasks in the harness.
_TEST_SEED = "test-seed-0123456789"

REPO = Path(__file__).resolve().parents[2]
TASKS = REPO / "tasks"
# 005 (network_assert) needs a live capture; covered separately in
# test_reference_graders.py with a faithful NetworkCapture fake. 009 now grades
# in dry-run too (static fallback of the behavioral Frida grader).
LIVE_ONLY = {"005-intercept-api-call"}


def _implemented():
    out = []
    for y in sorted(TASKS.glob("*/task.yaml")):
        if y.parent.name.startswith("_") or y.parent.name in LIVE_ONLY:
            continue
        meta = yaml.safe_load(y.read_text())
        if meta.get("grader_status") == "implemented":
            out.append((y.parent, meta))
    return out


def _correct_submission(pkg: Path, meta: dict) -> dict:
    # Seeded tasks have no static expected.json — regenerate the seed's answer.
    seeded = generate_challenge(pkg, _TEST_SEED)
    if seeded is not None:
        return {"value": seeded["answer"]}
    expected = json.loads((pkg / "grader" / "expected.json").read_text())
    if "frida" in expected:
        spec = expected["frida"]
        ret = spec.get("returns", "true")
        script = (
            "Java.perform(function(){"
            f'var C=Java.use("{spec.get("class","X")}");'
            f'C.{spec.get("method","m")}.implementation=function(){{ send("x"); return {ret}; }};'
            "});"
        )
        for needle in spec.get("must_contain", []):
            if needle not in script:
                script += f"/*{needle}*/"
        return {"script": script}
    value = expected.get("value") or expected.get("flag") or expected.get("secret")
    return {"value": value}


def test_every_implemented_task_grades_correct_and_wrong():
    tasks = _implemented()
    assert len(tasks) >= 22, f"expected the full curriculum implemented, got {len(tasks)}"
    runner = GradeRunner(emulator=None)
    for pkg, meta in tasks:
        ok = runner.grade(pkg, _correct_submission(pkg, meta), seed=_TEST_SEED)
        assert ok.passed, f"{pkg.name}: correct submission did not PASS ({ok.evidence})"

        wrong = {"script": "Java.perform(function(){});"} if meta["success_type"] == "frida_assert" \
            else {"value": "definitely-not-the-answer"}
        bad = runner.grade(pkg, wrong, seed=_TEST_SEED)
        assert not bad.passed, f"{pkg.name}: a wrong submission incorrectly PASSED"


def _decrypt(pkg: Path) -> str:
    art = pkg / "artifacts"
    if (art / "secret.enc").is_file():  # 031 — AES-CBC, IV prefixed
        blob = base64.b64decode((art / "secret.enc").read_text())
        iv, ct = blob[:16], blob[16:]
        key = bytes.fromhex("8f3c1d77a94b42e0b6c5e9f0a1d2c3b4")
        dec = Cipher(algorithms.AES(key), modes.CBC(iv)).decryptor()
    else:  # 032 — AES-ECB, static key
        ct = base64.b64decode((art / "weak.enc").read_text())
        dec = Cipher(algorithms.AES(b"masdojo_ecb_key!"), modes.ECB()).decryptor()
    pt = dec.update(ct) + dec.finalize()
    return pt[: -pt[-1]].decode()


@pytest.mark.parametrize("tid", ["031-decrypt-recovered-key", "032-break-weak-crypto"])
def test_crypto_tasks_are_actually_solvable(tid):
    pkg = TASKS / tid
    expected = json.loads((pkg / "grader" / "expected.json").read_text())["value"]
    assert _decrypt(pkg) == expected, f"{tid}: committed ciphertext does not decrypt to the flag"
