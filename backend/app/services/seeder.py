"""Load task packages from the `tasks/` directory into the database.

Idempotent: re-running upserts each task by id. Hint markdown is read from each
package's `hints/` directory and stored on the row so the API can serve hints
without filesystem access at request time. Solutions are stored too but gated by
the API (never returned before tier 3 / N failed attempts).
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml
from loguru import logger
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import SessionLocal
from app.models.task import Task

HINT_FILES = {1: "h1.md", 2: "h2.md", 3: "h3.md", 4: "solution.md"}


def _read_hints(package: Path) -> dict[str, str]:
    """Read available hint tiers from a package's hints/ directory."""
    hints: dict[str, str] = {}
    hint_dir = package / "hints"
    for tier, filename in HINT_FILES.items():
        path = hint_dir / filename
        if path.is_file():
            key = "solution" if tier == 4 else f"h{tier}"
            hints[key] = path.read_text(encoding="utf-8").strip()
    return hints


def _grader_status(package: Path, declared: str | None) -> str:
    """Decide whether a task's grader is implemented or a TODO scaffold."""
    if declared in {"implemented", "todo"}:
        return declared
    grade_py = package / "grader" / "grade.py"
    if grade_py.is_file():
        text = grade_py.read_text(encoding="utf-8")
        # A scaffolded grader is marked with a TODO sentinel.
        return "todo" if "TODO: implement grader" in text else "implemented"
    return "todo"


def _load_one(meta: dict[str, Any], package: Path, tasks_root: Path) -> dict[str, Any]:
    rel = package.relative_to(tasks_root.parent)
    return {
        "id": meta["id"],
        "title": meta.get("title", meta["id"]),
        "module": str(meta.get("module", "0")),
        "order_index": int(meta.get("order_index", 0)),
        "domain": meta.get("domain", "foundations"),
        "masvs": list(meta.get("masvs", [])),
        "mastg_refs": list(meta.get("mastg_refs", [])),
        "difficulty": int(meta.get("difficulty", 1)),
        "prereqs": list(meta.get("prereqs", [])),
        "objective": meta.get("objective", ""),
        "success_type": meta["success_type"],
        "submission_schema": dict(meta.get("submission_schema", {})),
        "time_estimate_min": int(meta.get("time_estimate_min", 20)),
        "hints": _read_hints(package),
        "is_reference": bool(meta.get("is_reference", False)),
        "grader_status": _grader_status(package, meta.get("grader_status")),
        "package_path": str(rel),
    }


def discover_packages(tasks_root: Path) -> list[Path]:
    """Return every task package (dir containing task.yaml), excluding _template."""
    packages: list[Path] = []
    for yaml_path in sorted(tasks_root.glob("*/task.yaml")):
        if yaml_path.parent.name.startswith("_"):
            continue
        packages.append(yaml_path.parent)
    return packages


def seed(db: Session, tasks_root: Path) -> int:
    if not tasks_root.is_dir():
        logger.warning("tasks directory not found at {}; skipping seed", tasks_root)
        return 0

    count = 0
    for package in discover_packages(tasks_root):
        meta_path = package / "task.yaml"
        try:
            meta = yaml.safe_load(meta_path.read_text(encoding="utf-8")) or {}
            if "id" not in meta or "success_type" not in meta:
                logger.error("task {} missing required id/success_type; skipping", package.name)
                continue
            values = _load_one(meta, package, tasks_root)
        except Exception as exc:  # noqa: BLE001 - keep seeding other tasks
            logger.exception("failed to load task package {}: {}", package.name, exc)
            continue

        existing = db.get(Task, values["id"])
        if existing:
            for key, val in values.items():
                setattr(existing, key, val)
        else:
            db.add(Task(**values))
        count += 1

    db.commit()
    logger.info("seeded {} task(s) from {}", count, tasks_root)
    return count


def run() -> None:
    from app.core.logging import configure_logging

    configure_logging()
    tasks_root = Path(settings.tasks_dir)
    with SessionLocal() as db:
        seed(db, tasks_root)


if __name__ == "__main__":
    run()
