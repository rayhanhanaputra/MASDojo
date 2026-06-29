"""Grader for 000 — APK Anatomy & Recon (static_assert).

Solvable by static analysis of the committed decoded resources (no device): the
learner reads the extracted strings.xml, recovers the flag, and submits it. We
confirm the value is correct AND that it genuinely lives in the shipped
resources, so the format alone can't be guessed.
"""

from __future__ import annotations

from runner.grader_api import Check, GradeResult, GradingContext, constant_time_equals


def grade(ctx: GradingContext) -> GradeResult:
    expected = ctx.artifacts.expected().get("flag", "")
    submitted = str(ctx.submission.get("value", "")).strip()

    matches = bool(expected) and constant_time_equals(submitted, expected)
    checks = [
        Check(
            name="recovered flag is correct",
            passed=matches,
            detail="exact match" if matches else "submitted value did not match the embedded flag",
        )
    ]

    strings_xml = ctx.package_dir / "artifacts" / "res" / "values" / "strings.xml"
    present = strings_xml.is_file() and expected.encode() in strings_xml.read_bytes()
    checks.append(
        Check(
            name="flag is genuinely present in the extracted resources",
            passed=present,
            detail="found in res/values/strings.xml" if present else "not found in the resources",
        )
    )

    passed = all(c.passed for c in checks)
    return GradeResult.from_checks(
        checks,
        "APK recon verified: flag recovered from the app resources."
        if passed
        else "The recovered value is not the flag embedded in this app's resources.",
    )
