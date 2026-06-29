"""Curriculum integrity guards — run in CI so coverage can't silently regress.

Enforces:
  - a task marked grader_status: implemented must NOT still contain the scaffold
    sentinel (and vice-versa) — no "claims implemented but ships the stub";
  - implemented comparison tasks (flag/static_assert) ship a grader/expected.json;
  - the prerequisite graph is complete (no dangling ids) and acyclic.
"""

from __future__ import annotations

from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parents[2]
TASKS = REPO / "tasks"
SENTINEL = "TODO: implement grader"
COMPARISON_TYPES = {"flag", "static_assert"}


def _packages():
    return [p.parent for p in sorted(TASKS.glob("*/task.yaml")) if not p.parent.name.startswith("_")]


def _meta(pkg: Path) -> dict:
    return yaml.safe_load((pkg / "task.yaml").read_text(encoding="utf-8")) or {}


def test_implemented_status_matches_grader():
    problems = []
    for pkg in _packages():
        meta = _meta(pkg)
        declared = meta.get("grader_status")
        grade_py = pkg / "grader" / "grade.py"
        has_sentinel = grade_py.is_file() and SENTINEL in grade_py.read_text(encoding="utf-8")
        if declared == "implemented" and has_sentinel:
            problems.append(f"{pkg.name}: grader_status=implemented but grade.py still has the TODO sentinel")
        if declared == "todo" and grade_py.is_file() and not has_sentinel:
            problems.append(f"{pkg.name}: grader_status=todo but grade.py has no sentinel (looks implemented)")
    assert not problems, "grader status drift:\n  " + "\n  ".join(problems)


def test_implemented_comparison_tasks_have_expected_json():
    problems = []
    for pkg in _packages():
        meta = _meta(pkg)
        if meta.get("grader_status") == "implemented" and meta.get("success_type") in COMPARISON_TYPES:
            if not (pkg / "grader" / "expected.json").is_file():
                problems.append(f"{pkg.name}: implemented {meta.get('success_type')} task missing grader/expected.json")
    assert not problems, "missing expected.json:\n  " + "\n  ".join(problems)


def test_prereq_dag_is_complete_and_acyclic():
    metas = {p.name: _meta(p) for p in _packages()}
    ids = {m["id"] for m in metas.values()}

    dangling = []
    graph = {}
    for m in metas.values():
        graph[m["id"]] = list(m.get("prereqs", []))
        for pr in m.get("prereqs", []):
            if pr not in ids:
                dangling.append(f"{m['id']} -> {pr}")
    assert not dangling, "dangling prereqs: " + ", ".join(dangling)

    # cycle detection
    WHITE, GREY, BLACK = 0, 1, 2
    color = {k: WHITE for k in graph}
    cycle = []

    def visit(node):
        color[node] = GREY
        for nxt in graph.get(node, []):
            if color[nxt] == GREY:
                cycle.append(f"{node} -> {nxt}")
                return True
            if color[nxt] == WHITE and visit(nxt):
                return True
        color[node] = BLACK
        return False

    assert not any(visit(n) for n in graph if color[n] == WHITE), f"prereq cycle: {cycle}"
