"""Capstone grader — the final flag is released only by the live admin vault
(vulnapi /admin/vault) after the learner chains the earlier techniques. It is not
present in any committed file."""
from __future__ import annotations

from runner.graders import grade_flag


def grade(ctx):
    return grade_flag(ctx)
