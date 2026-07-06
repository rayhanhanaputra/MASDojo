"""Runner configuration sourced from environment variables."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


def _int(name: str, default: int) -> int:
    try:
        return int(os.environ.get(name, default))
    except (TypeError, ValueError):
        return default


@dataclass(frozen=True)
class RunnerConfig:
    redis_url: str = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
    grading_queue: str = os.environ.get("GRADING_QUEUE", "masdojo:grading")
    database_url: str = os.environ.get(
        "DATABASE_URL", "postgresql+psycopg://masdojo:masdojo@localhost:5432/masdojo"
    )

    tasks_root: Path = Path(os.environ.get("TASKS_ROOT", "/app/tasks"))
    artifacts_dir: Path = Path(os.environ.get("ARTIFACTS_DIR", "/app/artifacts"))

    job_timeout_sec: int = _int("GRADING_JOB_TIMEOUT_SEC", 420)

    avd_name: str = os.environ.get("AVD_NAME", "masdojo_avd")
    android_sdk_root: Path = Path(os.environ.get("ANDROID_SDK_ROOT", "/opt/android-sdk"))
    frida_version: str = os.environ.get("FRIDA_VERSION", "16.4.8")
    mitm_port: int = _int("MITM_PORT", 8081)
    emulator_serial: str = os.environ.get("EMULATOR_SERIAL", "emulator-5554")

    # When true, the runner does not drive a real emulator. Used for unit tests
    # and for environments without KVM; graders that don't need a live device
    # (flag/static_assert) still grade correctly.
    dry_run: bool = os.environ.get("RUNNER_DRY_RUN", "false").lower() in {"1", "true", "yes"}

    # When true, the runner ATTACHES to an already-running AVD (provisioned by
    # `make avd-up` on the participant's host) instead of booting + snapshotting
    # its own. This is the local single-participant model: the emulator is owned
    # by the participant, the runner just grades against it.
    attach_mode: bool = os.environ.get("RUNNER_ATTACH", "false").lower() in {"1", "true", "yes"}


config = RunnerConfig()
