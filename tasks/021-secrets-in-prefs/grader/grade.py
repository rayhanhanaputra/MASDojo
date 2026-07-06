"""Grader for 021-secrets-in-prefs — seeded payload detection.

This task is *per-learner seeded*: each learner's SharedPreferences dump carries
a different auth token (see challenge/generate.py). The grader regenerates this
learner's target from their seed and checks the submission against it, so a token
shared by another learner never passes — the lab is a real assessment.
"""
from __future__ import annotations

from runner.graders import grade_seeded_recovered


def grade(ctx):
    return grade_seeded_recovered(ctx)
