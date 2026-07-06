"""Seeded grader — the credential is base64 in the one cleartext (http) request;
the learner must find it and decode it, not read a plaintext flag."""
from __future__ import annotations

from runner.graders import grade_seeded_recovered


def grade(ctx):
    return grade_seeded_recovered(ctx)
