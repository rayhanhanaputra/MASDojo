"""Tests for the reusable comparison graders."""

from __future__ import annotations

import json
from pathlib import Path

from loguru import logger

from runner.grader_api import GradingContext
from runner.graders import grade_flag, grade_static


def _ctx(tmp_path: Path, expected: dict, submission: dict) -> GradingContext:
    (tmp_path / "grader").mkdir(parents=True, exist_ok=True)
    (tmp_path / "grader" / "expected.json").write_text(json.dumps(expected))
    return GradingContext.build(submission=submission, package_dir=tmp_path, log=logger)


def test_grade_flag_pass(tmp_path: Path):
    r = grade_flag(_ctx(tmp_path, {"flag": "FLAG{ok}"}, {"flag": "FLAG{ok}"}))
    assert r.passed and r.checks[0].passed


def test_grade_flag_fail(tmp_path: Path):
    r = grade_flag(_ctx(tmp_path, {"flag": "FLAG{ok}"}, {"flag": "FLAG{nope}"}))
    assert not r.passed


def test_grade_flag_accepts_value_field(tmp_path: Path):
    # submission may carry the answer under 'value' too
    r = grade_flag(_ctx(tmp_path, {"flag": "FLAG{ok}"}, {"value": "FLAG{ok}"}))
    assert r.passed


def test_grade_static_pass(tmp_path: Path):
    r = grade_static(_ctx(tmp_path, {"secret": "s3cr3t"}, {"value": "s3cr3t"}))
    assert r.passed


def test_grade_misconfigured_no_expected(tmp_path: Path):
    r = grade_flag(_ctx(tmp_path, {}, {"flag": "x"}))
    assert not r.passed
    assert "misconfigured" in r.evidence.lower()
