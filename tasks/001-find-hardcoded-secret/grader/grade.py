"""Grader for 001 — Find the Hardcoded API Secret (static_assert).

The learner submits the API key they recovered by decompiling the APK. We
compare it (constant time) against the true embedded secret. When a live device
/ APK is available we additionally confirm the value is genuinely present in the
target APK, so a lucky guess of the format alone can't pass.
"""

from __future__ import annotations

import zipfile

from runner.grader_api import Check, GradeResult, GradingContext, constant_time_equals


def _present_in_apk(ctx: GradingContext, secret: str) -> bool | None:
    """Best-effort check that the secret really lives in the APK.

    An APK is a ZIP: its classes.dex (where a BuildConfig string constant lands)
    is stored DEFLATED, so the key never appears as contiguous bytes in the raw
    file — scanning `apk.read_bytes()` directly always missed it and failed every
    correct answer. Decompress each entry and scan the inflated bytes instead.

    Returns True/False when we can inspect the APK, or None when we can't (e.g.
    dry-run with no artifact), so the caller can skip the check gracefully.
    """
    apk = ctx.artifacts.apk_path
    if not apk.is_file():
        return None
    needle = secret.encode()
    try:
        with zipfile.ZipFile(apk) as zf:
            for name in zf.namelist():
                try:
                    if needle in zf.read(name):
                        return True
                except (OSError, zipfile.BadZipFile, RuntimeError):
                    continue
        return False
    except (OSError, zipfile.BadZipFile):
        return None


def grade(ctx: GradingContext) -> GradeResult:
    expected = ctx.artifacts.expected().get("secret", "")
    submitted = str(ctx.submission.get("value", "")).strip()

    checks: list[Check] = []

    matches = bool(expected) and constant_time_equals(submitted, expected)
    checks.append(
        Check(
            name="recovered key matches the embedded secret",
            passed=matches,
            detail="exact match" if matches else "submitted value did not match the embedded key",
        )
    )

    present = _present_in_apk(ctx, expected)
    if present is not None:
        checks.append(
            Check(
                name="secret is genuinely embedded in the APK",
                passed=present,
                detail="found the key bytes inside target.apk"
                if present
                else "could not locate the key inside target.apk",
            )
        )

    passed = all(c.passed for c in checks)
    evidence = (
        "Recovered API key verified against the embedded secret."
        if passed
        else "The submitted value is not the API key embedded in this app."
    )
    return GradeResult.from_checks(checks, evidence)
