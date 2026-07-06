"""Grader for 072 — JWT alg:none forgery. The flag is not in any committed file:
the learner forges an unsigned admin token against the live vulnapi and submits
the value /admin/ledger returns."""
from __future__ import annotations

from runner.graders import grade_flag


def grade(ctx):
    return grade_flag(ctx)
