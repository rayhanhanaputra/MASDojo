"""The grading contract shared by every task grader.

A task's `grader/grade.py` implements:

    def grade(ctx: GradingContext) -> GradeResult: ...

`GradingContext` exposes everything a grader needs:

  ctx.submission   - the learner's submitted payload (dict)
  ctx.package_dir  - Path to this task package on disk
  ctx.artifacts    - read expected values / files bundled with the task
  ctx.adb          - run adb commands against the booted AVD
  ctx.frida        - inject/run Frida scripts in the target process
  ctx.network      - captured mitmproxy flows (network_assert tasks)
  ctx.log          - structured logger

Graders must be deterministic and side-effect-free beyond reading the device.
Return concrete `Check` entries so the learner sees exactly what passed/failed.
"""

from __future__ import annotations

import hmac
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Any, Protocol

if TYPE_CHECKING:  # avoid hard runtime deps for graders that don't touch a device
    from runner.adb import AdbClient
    from runner.frida_client import FridaClient
    from runner.network import NetworkCapture


@dataclass
class Check:
    """A single graded condition shown to the learner."""

    name: str
    passed: bool
    detail: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {"name": self.name, "passed": self.passed, "detail": self.detail}


@dataclass
class GradeResult:
    """The outcome of grading a submission."""

    passed: bool
    evidence: str
    checks: list[Check] = field(default_factory=list)
    score: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "passed": self.passed,
            "evidence": self.evidence,
            "checks": [c.to_dict() for c in self.checks],
            "score": self.score,
        }

    @classmethod
    def from_checks(cls, checks: list[Check], evidence: str) -> "GradeResult":
        """Build a result that passes only if every check passed."""
        passed = all(c.passed for c in checks)
        return cls(passed=passed, evidence=evidence, checks=checks)


class Artifacts:
    """Read-only access to files bundled with the task package.

    Expected grading values live in `grader/expected.json` (never shipped to the
    frontend). Graders read them through here so secrets stay server-side.
    """

    def __init__(self, package_dir: Path) -> None:
        self._dir = package_dir

    @property
    def apk_path(self) -> Path:
        return self._dir / "app" / "target.apk"

    def expected(self) -> dict[str, Any]:
        path = self._dir / "grader" / "expected.json"
        if not path.is_file():
            return {}
        return json.loads(path.read_text(encoding="utf-8"))

    def read_text(self, relative: str) -> str:
        return (self._dir / relative).read_text(encoding="utf-8")


def constant_time_equals(a: str, b: str) -> bool:
    """Constant-time string comparison for flag/secret checks."""
    return hmac.compare_digest(a.strip().encode(), b.strip().encode())


class _NullDevice:
    """Stand-in used when a grader accesses a device facet that isn't wired up
    (e.g. a static grader in dry-run). Any call raises a clear error."""

    def __init__(self, facet: str) -> None:
        self._facet = facet

    def __getattr__(self, name: str) -> Any:
        raise RuntimeError(
            f"grader accessed ctx.{self._facet}.{name} but no live device is available"
        )


class DeviceAdb(Protocol):  # pragma: no cover - structural typing only
    def shell(self, command: str) -> str: ...
    def pull(self, remote: str, local: str) -> Path: ...


@dataclass
class GradingContext:
    submission: dict[str, Any]
    package_dir: Path
    artifacts: Artifacts
    log: Any
    adb: "AdbClient | _NullDevice"
    frida: "FridaClient | _NullDevice"
    network: "NetworkCapture | _NullDevice"

    @classmethod
    def build(
        cls,
        *,
        submission: dict[str, Any],
        package_dir: Path,
        log: Any,
        adb: Any = None,
        frida: Any = None,
        network: Any = None,
    ) -> "GradingContext":
        # Use explicit None checks: a live facet can be legitimately falsy (an
        # empty NetworkCapture has len 0) and must not be replaced by a null stub.
        return cls(
            submission=submission,
            package_dir=package_dir,
            artifacts=Artifacts(package_dir),
            log=log,
            adb=adb if adb is not None else _NullDevice("adb"),
            frida=frida if frida is not None else _NullDevice("frida"),
            network=network if network is not None else _NullDevice("network"),
        )
