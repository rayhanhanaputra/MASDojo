"""Grader for 009 — Root Detection Bypass (frida_assert).

Uses the platform's behavioral grader: the app is run once with no hook to prove
it genuinely gates on this device (baseline locked), then again with the
learner's Frida script to prove their hook flips the guard at runtime (unlocked).
A pass means the bypass is *attributable to the submitted script*, not to the
environment — and the full baseline→hook evidence bundle backs the verdict.

In dry-run (no KVM) it falls back to static validation of the script so the task
stays solvable for self-study.
"""

from __future__ import annotations

from runner.grader_api import GradeResult, GradingContext
from runner.graders import grade_frida_behavioral


def grade(ctx: GradingContext) -> GradeResult:
    return grade_frida_behavioral(ctx)
