"""Grader for 071-idor-backend — payload detection (recovered value).

Verifies the learner recovered the correct value by applying the technique, and
(where artifacts are committed) that the value genuinely lives in them.
"""
from __future__ import annotations

from runner.graders import grade_recovered


def grade(ctx):
    return grade_recovered(ctx)
