"""Dry-run tests for the grader framework: loading, context, pass/fail.

These run without an emulator (RUNNER_DRY_RUN), proving the grading contract and
the flag/static_assert path end to end.
"""

from __future__ import annotations

import json
import textwrap
from pathlib import Path

import pytest

from runner.grade_runner import GradeRunner, GraderLoadError

FLAG_GRADER = textwrap.dedent(
    """
    from runner.grader_api import Check, GradeResult, GradingContext, constant_time_equals

    def grade(ctx: GradingContext) -> GradeResult:
        expected = ctx.artifacts.expected().get("flag", "")
        submitted = ctx.submission.get("flag", "")
        ok = constant_time_equals(submitted, expected)
        check = Check(name="flag matches", passed=ok,
                      detail="correct flag" if ok else "flag did not match")
        return GradeResult.from_checks([check],
            evidence="Flag accepted." if ok else "Flag rejected.")
    """
)


def _make_task(root: Path, *, success_type: str, grader: str, expected: dict) -> Path:
    pkg = root / "task-001"
    (pkg / "grader").mkdir(parents=True)
    (pkg / "app").mkdir(parents=True)
    (pkg / "task.yaml").write_text(
        f"id: task-001\ntitle: T\nsuccess_type: {success_type}\ndifficulty: 1\n"
    )
    (pkg / "grader" / "grade.py").write_text(grader)
    (pkg / "grader" / "expected.json").write_text(json.dumps(expected))
    return pkg


def test_flag_grader_passes_on_correct_submission(tmp_path: Path):
    pkg = _make_task(tmp_path, success_type="flag", grader=FLAG_GRADER,
                     expected={"flag": "FLAG{hello}"})
    result = GradeRunner(emulator=None).grade(pkg, {"flag": "FLAG{hello}"})
    assert result.passed is True
    assert result.checks[0].passed is True
    assert "accepted" in result.evidence.lower()


def test_flag_grader_fails_on_wrong_submission(tmp_path: Path):
    pkg = _make_task(tmp_path, success_type="flag", grader=FLAG_GRADER,
                     expected={"flag": "FLAG{hello}"})
    result = GradeRunner(emulator=None).grade(pkg, {"flag": "FLAG{nope}"})
    assert result.passed is False
    assert result.checks[0].passed is False


def test_missing_grader_raises(tmp_path: Path):
    pkg = tmp_path / "empty"
    (pkg).mkdir()
    (pkg / "task.yaml").write_text("id: empty\nsuccess_type: flag\n")
    with pytest.raises(GraderLoadError):
        GradeRunner(emulator=None).grade(pkg, {})


def test_grader_must_return_grade_result(tmp_path: Path):
    bad = "def grade(ctx):\n    return 'nope'\n"
    pkg = _make_task(tmp_path, success_type="flag", grader=bad, expected={})
    with pytest.raises(GraderLoadError):
        GradeRunner(emulator=None).grade(pkg, {})
