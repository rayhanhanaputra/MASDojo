"""Grader for 071 — IDOR. The flag is not in any committed file: the learner must
exploit the live vulnerable API (vulnapi) and submit the value it returns."""
from __future__ import annotations

from runner.graders import grade_flag


def grade(ctx):
    return grade_flag(ctx)
