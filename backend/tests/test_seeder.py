"""Tests for the task package loader/seeder."""

from __future__ import annotations

from pathlib import Path

import yaml

from app.db.session import SessionLocal
from app.models.task import Task
from app.services.seeder import seed


def _write_task(root: Path, slug: str, *, grader_body: str, declared: str | None = None) -> None:
    pkg = root / slug
    (pkg / "hints").mkdir(parents=True)
    (pkg / "grader").mkdir(parents=True)
    meta = {
        "id": slug,
        "title": "Sample Task",
        "module": "1",
        "order_index": 1,
        "domain": "static-re",
        "masvs": ["MASVS-STORAGE-1"],
        "mastg_refs": ["MASTG-TECH-0001"],
        "difficulty": 2,
        "prereqs": [],
        "objective": "Do the thing.",
        "success_type": "static_assert",
        "submission_schema": {"value": "string"},
        "time_estimate_min": 15,
    }
    if declared:
        meta["grader_status"] = declared
    (pkg / "task.yaml").write_text(yaml.safe_dump(meta))
    (pkg / "hints" / "h1.md").write_text("nudge")
    (pkg / "hints" / "h2.md").write_text("pointer")
    (pkg / "hints" / "h3.md").write_text("steps")
    (pkg / "hints" / "solution.md").write_text("the answer is 42")
    (pkg / "grader" / "grade.py").write_text(grader_body)


def test_seed_loads_task_and_detects_implemented(tmp_path: Path):
    tasks_root = tmp_path / "tasks"
    tasks_root.mkdir()
    _write_task(tasks_root, "001-real", grader_body="def grade(ctx):\n    return None\n")
    _write_task(
        tasks_root,
        "002-scaffold",
        grader_body="def grade(ctx):\n    # TODO: implement grader\n    return None\n",
    )
    # _template-style dirs are skipped.
    (tasks_root / "_template").mkdir()

    with SessionLocal() as db:
        count = seed(db, tasks_root)
        assert count == 2

        real = db.get(Task, "001-real")
        assert real is not None
        assert real.grader_status == "implemented"
        assert real.hints["h1"] == "nudge"
        assert real.hints["solution"] == "the answer is 42"
        assert real.masvs == ["MASVS-STORAGE-1"]

        scaffold = db.get(Task, "002-scaffold")
        assert scaffold.grader_status == "todo"


def test_seed_is_idempotent(tmp_path: Path):
    tasks_root = tmp_path / "tasks"
    tasks_root.mkdir()
    _write_task(tasks_root, "001-real", grader_body="def grade(ctx):\n    return None\n")

    with SessionLocal() as db:
        assert seed(db, tasks_root) == 1
        assert seed(db, tasks_root) == 1
        assert db.query(Task).count() == 1
