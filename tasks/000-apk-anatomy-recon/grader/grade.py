"""Seeded grader — the recon flag is base64-encoded in the decoded resources; the
learner must find and decode it, not copy a plaintext string."""
from __future__ import annotations

from runner.graders import grade_seeded_recovered


def grade(ctx):
    return grade_seeded_recovered(ctx)
