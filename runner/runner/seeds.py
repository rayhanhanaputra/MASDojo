"""Per-learner challenge seeding (runner side).

`derive_seed` is duplicated verbatim from the backend (`app/core/seeds.py`) —
both services must derive the identical seed for a learner so the artifact the
learner downloaded and the answer the grader expects come from the same seed.
Keep the two copies in sync.
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

    Mixes INSTALL_SALT (identical env var the backend reads) so a given install
    produces the same target in both services, but different installs differ.
    """
    install = os.environ.get("INSTALL_SALT", "")
    return hashlib.sha256(f"{_SALT}:{install}:{user_id}:{task_id}".encode()).hexdigest()


def generate_challenge(package_dir: Path, seed: str) -> dict[str, Any] | None:
    """Run the task's seeded generator, or None if the task isn't seeded."""
    gen = package_dir / "challenge" / "generate.py"
    if not gen.is_file():
        return None
    spec = importlib.util.spec_from_file_location(f"challenge_{package_dir.name}", gen)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.generate(seed)
