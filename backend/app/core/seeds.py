"""Per-learner challenge seeding — the anti-memorization layer.

A *seeded* task ships a server-side `challenge/generate.py` instead of static
`artifacts/` + a fixed answer. Given a per-(learner, task) seed, the generator
produces that learner's own artifact files and the answer they must recover, so:

  - every learner gets a different target (a shared answer is useless), and
  - the grader regenerates the same answer from the same seed and checks it.

The generator is never shipped to the client (only `artifacts/` is served), so a
learner receives only their generated files and must actually apply the
technique to extract the answer.

`derive_seed` is duplicated verbatim in the runner (`runner/seeds.py`) — both
services must derive the identical seed for a learner. Keep them in sync.
"""

from __future__ import annotations

import hashlib
import importlib.util
import os
from pathlib import Path
from typing import Any

_SALT = "masdojo-seed:v1"


def derive_seed(user_id: int, task_id: str) -> str:
    """Deterministic, per-(learner, task) seed. Same everywhere for one learner.

    INSTALL_SALT differentiates installs so participants get distinct targets
    even in solo mode (one fixed profile). Empty by default (no differentiation).
    """
    install = os.environ.get("INSTALL_SALT", "")
    return hashlib.sha256(f"{_SALT}:{install}:{user_id}:{task_id}".encode()).hexdigest()


def generator_path(package_dir: Path) -> Path:
    return package_dir / "challenge" / "generate.py"


def is_seeded(package_dir: Path) -> bool:
    return generator_path(package_dir).is_file()


def generate_challenge(package_dir: Path, seed: str) -> dict[str, Any] | None:
    """Run the task's seeded generator, or None if the task isn't seeded.

    Returns {"answer": str, "files": {relpath: content}, "present_in": [relpath]}.
    """
    gen = generator_path(package_dir)
    if not gen.is_file():
        return None
    spec = importlib.util.spec_from_file_location(f"challenge_{package_dir.name}", gen)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.generate(seed)
