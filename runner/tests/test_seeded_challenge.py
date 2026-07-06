"""Seeded challenges: the anti-memorization guarantee, across every seeded task.

Two learners get different targets from the same task, and the value one learner
recovers does NOT solve the other's challenge — so answer-sharing is useless and
the lab behaves as a real assessment. Exercised end-to-end through each real
seeded grader.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest
from loguru import logger

from runner.grader_api import GradingContext
from runner.seeds import derive_seed, generate_challenge

REPO = Path(__file__).resolve().parents[2]
TASKS = REPO / "tasks"

# Every task that ships a seeded generator.
SEEDED = sorted(p.parent.parent.name for p in TASKS.glob("*/challenge/generate.py"))


def _grade(task_dir: Path, submission, seed):
    spec = importlib.util.spec_from_file_location(f"g_{task_dir.name}", task_dir / "grader" / "grade.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.grade(
        GradingContext.build(submission=submission, package_dir=task_dir, log=logger, seed=seed)
    )


def test_there_are_seeded_tasks():
    assert len(SEEDED) >= 4, f"expected several seeded tasks, found {SEEDED}"


@pytest.mark.parametrize("tid", SEEDED)
def test_two_learners_get_different_targets(tid):
    task = TASKS / tid
    a = generate_challenge(task, derive_seed(1, tid))
    b = generate_challenge(task, derive_seed(2, tid))
    assert a["answer"] != b["answer"], f"{tid}: distinct learners must get distinct secrets"
    # The secret really is embedded in each learner's own served file(s).
    for spec in (a, b):
        assert any(spec["answer"] in c for c in spec["files"].values()), f"{tid}: answer not in files"


@pytest.mark.parametrize("tid", SEEDED)
def test_own_value_passes_shared_value_fails(tid):
    task = TASKS / tid
    seed_a = derive_seed(1, tid)
    seed_b = derive_seed(2, tid)
    answer_a = generate_challenge(task, seed_a)["answer"]

    # A's own value passes for A.
    ok = _grade(task, {"value": answer_a, "flag": answer_a}, seed_a)
    assert ok.passed is True, f"{tid}: own value should pass ({ok.evidence})"

    # A's value shared to B fails for B.
    bad = _grade(task, {"value": answer_a, "flag": answer_a}, seed_b)
    assert bad.passed is False, f"{tid}: a shared value must not pass another learner"


def test_seed_is_deterministic():
    assert derive_seed(42, "x") == derive_seed(42, "x")
    assert derive_seed(42, "x") != derive_seed(43, "x")
    assert derive_seed(42, "x") != derive_seed(42, "y")
