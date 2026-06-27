"""Grader scaffold for 031-decrypt-recovered-key — implement grade(ctx) -> GradeResult.

See runner/runner/grader_api.py for the contract and tasks/001, 005, 009 for
fully-worked reference graders of each success type.
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
