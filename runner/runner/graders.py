"""Reusable grader helpers so a task's grade.py is a one-liner for the common
comparison cases.

A `flag` or `static_assert` task usually just needs: read the expected value
from the task's server-side `grader/expected.json`, constant-time compare it
against the learner's submission, and return a single Check. These helpers
provide exactly that, so authoring a new comparison task is:

    from runner.graders import grade_flag
    def grade(ctx):
        return grade_flag(ctx)

These run fully in dry-run (no device): they only touch ctx.submission and the
task's expected values.
"""

from __future__ import annotations

from runner.grader_api import Check, GradeResult, GradingContext, constant_time_equals

# Submission fields we accept, in priority order, for a comparison grader.
_SUBMIT_FIELDS = ("flag", "value", "secret")


def _submitted(ctx: GradingContext) -> str:
    for field in _SUBMIT_FIELDS:
        val = ctx.submission.get(field)
        if isinstance(val, str) and val.strip():
            return val.strip()
    return ""


def _expected(ctx: GradingContext, fields: tuple[str, ...]) -> str:
    data = ctx.artifacts.expected()
    for field in fields:
        val = data.get(field)
        if isinstance(val, str) and val:
            return val
    return ""


def grade_comparison(
    ctx: GradingContext,
    *,
    expected_fields: tuple[str, ...],
    check_name: str,
) -> GradeResult:
    """Constant-time compare the submission against the task's expected value."""
    expected = _expected(ctx, expected_fields)
    submitted = _submitted(ctx)
    if not expected:
        return GradeResult(
            passed=False,
            evidence="Task misconfigured: no expected value in grader/expected.json.",
            checks=[Check(check_name, False, "grader/expected.json is missing the expected value")],
        )
    ok = constant_time_equals(submitted, expected)
    return GradeResult.from_checks(
        [Check(check_name, ok, "exact match" if ok else "submitted value did not match")],
        "Accepted." if ok else "Rejected: the submitted value is not correct.",
    )


def grade_flag(ctx: GradingContext) -> GradeResult:
    """Grade a `flag` task against `flag` (or `value`) in expected.json."""
    return grade_comparison(ctx, expected_fields=("flag", "value"), check_name="flag matches expected")


def grade_static(ctx: GradingContext) -> GradeResult:
    """Grade a `static_assert` task against `secret`/`value` in expected.json."""
    return grade_comparison(
        ctx, expected_fields=("secret", "value", "flag"), check_name="recovered value is correct"
    )
