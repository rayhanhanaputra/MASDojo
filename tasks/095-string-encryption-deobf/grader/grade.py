"""Seeded payload-detection grader — the answer is derived (XOR-deobfuscated)
from the per-learner challenge, never copied from it verbatim.
"""
from __future__ import annotations

from runner.graders import grade_seeded_recovered


def grade(ctx):
    return grade_seeded_recovered(ctx)
