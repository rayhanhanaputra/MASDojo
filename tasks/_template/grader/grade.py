"""Grader scaffold. Implement grade(ctx) -> GradeResult for this task.

The grading contract is defined in runner/runner/grader_api.py. A grader receives
a GradingContext exposing:

  ctx.submission   - the learner's submitted payload (dict)
  ctx.adb          - helper to run adb commands against the booted AVD
  ctx.frida        - helper to inject/run Frida scripts in the target process
  ctx.network      - captured mitmproxy flows (for network_assert tasks)
  ctx.artifacts    - paths to task artifacts (apk, expected values, etc.)
  ctx.package_dir  - path to this task package on disk

Return a GradeResult(passed, evidence, checks, score). Use Check(name, passed,
detail) entries so the learner sees exactly which condition passed or failed.
"""

from __future__ import annotations

from runner.grader_api import Check, GradeResult, GradingContext


def grade(ctx: GradingContext) -> GradeResult:
    # TODO: implement grader
    return GradeResult(
        passed=False,
        evidence="Grader not implemented for this scaffolded task.",
        checks=[Check(name="implemented", passed=False, detail="This task is a scaffold.")],
        score=0,
    )
