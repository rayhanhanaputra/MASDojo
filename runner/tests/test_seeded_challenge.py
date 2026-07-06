"""Seeded challenges: the anti-memorization guarantee.

Two learners get different targets from the same task, and the value one learner
recovers does NOT solve the other's challenge — so answer-sharing is useless and
the lab behaves as a real assessment. Exercised end-to-end through the real
grader for task 021.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

from loguru import logger

from runner.grader_api import GradingContext
from runner.seeds import derive_seed, generate_challenge

REPO = Path(__file__).resolve().parents[2]
TASK = REPO / "tasks" / "021-secrets-in-prefs"


def _grade(submission, seed):
    spec = importlib.util.spec_from_file_location("g021", TASK / "grader" / "grade.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.grade(
        GradingContext.build(submission=submission, package_dir=TASK, log=logger, seed=seed)
    )


def test_two_learners_get_different_targets():
    a = generate_challenge(TASK, derive_seed(1, "021-secrets-in-prefs"))
    b = generate_challenge(TASK, derive_seed(2, "021-secrets-in-prefs"))
    assert a["answer"] != b["answer"], "distinct learners must get distinct secrets"
    # The secret really is embedded in each learner's own served file.
    assert a["answer"] in a["files"]["shared_prefs/auth.xml"]
    assert b["answer"] in b["files"]["shared_prefs/auth.xml"]


def test_correct_value_passes_for_own_seed():
    seed = derive_seed(7, "021-secrets-in-prefs")
    answer = generate_challenge(TASK, seed)["answer"]
    result = _grade({"value": answer}, seed)
    assert result.passed is True
    assert all(c.passed for c in result.checks)


def test_shared_value_fails_for_another_learner():
    seed_a = derive_seed(1, "021-secrets-in-prefs")
    seed_b = derive_seed(2, "021-secrets-in-prefs")
    answer_a = generate_challenge(TASK, seed_a)["answer"]
    # Learner B submits learner A's leaked token -> must FAIL against B's seed.
    result = _grade({"value": answer_a}, seed_b)
    assert result.passed is False


def test_seed_is_deterministic():
    assert derive_seed(42, "021-secrets-in-prefs") == derive_seed(42, "021-secrets-in-prefs")
    assert derive_seed(42, "021-secrets-in-prefs") != derive_seed(43, "021-secrets-in-prefs")
