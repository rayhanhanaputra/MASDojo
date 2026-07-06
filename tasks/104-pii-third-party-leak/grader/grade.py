"""Seeded payload-detection grader for 104 — PII leaked to a third-party SDK.

Per-learner seeded: each learner's captured request exfiltrates a different user
email (see challenge/generate.py). The grader regenerates this learner's target
from their seed and checks the submission against it, so a shared value never
passes.
"""
from __future__ import annotations

from runner.graders import grade_seeded_recovered


def grade(ctx):
    return grade_seeded_recovered(ctx)
