"""Seeded payload-detection grader.

This task is per-learner seeded: each learner's artifact embeds a different
secret (see challenge/generate.py). The grader regenerates this learner's target
from their seed and checks the submission against it, so a value shared from
another learner never passes.
"""
from __future__ import annotations

from runner.graders import grade_seeded_recovered


def grade(ctx):
    return grade_seeded_recovered(ctx)
