"""Load a task's grader, prepare the device for its success type, and run it.

Responsibilities split:
  - grade_runner sets up the *environment* (boot/restore AVD, install APK,
    start network capture, etc.) according to the task's `success_type`.
  - the task's `grade.py` performs the *assertions* via the GradingContext.

In dry-run mode (no KVM / unit tests) device facets are null; `flag` and
`static_assert` graders still grade correctly because they only compare the
submission against the task's expected values.
"""

from __future__ import annotations

import importlib.util
import time
from pathlib import Path
from types import ModuleType
from typing import Any

import yaml
from loguru import logger

from runner.config import config
from runner.grader_api import GradeResult, GradingContext


class GraderLoadError(RuntimeError):
    pass


def _load_grader_module(package_dir: Path) -> ModuleType:
    grade_py = package_dir / "grader" / "grade.py"
    if not grade_py.is_file():
        raise GraderLoadError(f"no grader at {grade_py}")
    spec = importlib.util.spec_from_file_location(
        f"masdojo_grader_{package_dir.name}", grade_py
    )
    if spec is None or spec.loader is None:  # pragma: no cover - defensive
        raise GraderLoadError(f"could not load grader spec for {grade_py}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    if not hasattr(module, "grade"):
        raise GraderLoadError(f"grader {grade_py} does not define grade(ctx)")
    return module


def _read_meta(package_dir: Path) -> dict[str, Any]:
    return yaml.safe_load((package_dir / "task.yaml").read_text(encoding="utf-8")) or {}


class GradeRunner:
    """Orchestrates a single grading job against a (possibly mocked) device."""

    def __init__(self, emulator: Any = None) -> None:
        # `emulator` is an EmulatorManager when a live device is available.
        self._emulator = emulator

    def grade(self, package_dir: Path, submission: dict[str, Any]) -> GradeResult:
        meta = _read_meta(package_dir)
        success_type = meta.get("success_type", "flag")
        module = _load_grader_module(package_dir)

        adb = self._emulator.adb if self._emulator else None
        live = self._emulator is not None and not config.dry_run

        if not live:
            logger.info("grading {} in dry-run (no live device)", package_dir.name)
            ctx = GradingContext.build(
                submission=submission, package_dir=package_dir, log=logger
            )
            return self._call(module, ctx)

        # Live device path: restore a clean snapshot and install the target.
        self._emulator.restore_snapshot()
        adb.install(package_dir / "app" / "target.apk")

        if success_type == "network_assert":
            return self._grade_network(module, meta, package_dir, submission, adb)
        return self._grade_device(module, meta, package_dir, submission, adb)

    def _grade_device(self, module, meta, package_dir, submission, adb) -> GradeResult:
        from runner.frida_client import FridaClient

        frida = None
        if meta.get("success_type") == "frida_assert":
            frida = FridaClient(config.emulator_serial)
        ctx = GradingContext.build(
            submission=submission,
            package_dir=package_dir,
            log=logger,
            adb=adb,
            frida=frida,
        )
        return self._call(module, ctx)

    def _grade_network(self, module, meta, package_dir, submission, adb) -> GradeResult:
        from runner.network import MitmProxyRecorder

        package = meta.get("app_package")
        activity = meta.get("launch_activity")
        wait_sec = int(meta.get("interaction_wait_sec", 15))
        flow_path = config.artifacts_dir / f"{package_dir.name}.flows"

        with MitmProxyRecorder(config.mitm_port, flow_path) as recorder:
            # Route the device's HTTP(S) traffic through mitmproxy.
            adb.shell(f"settings put global http_proxy 10.0.2.2:{config.mitm_port}")
            if package:
                adb.launch_app(package, activity)
            logger.info("network interaction window: {}s", wait_sec)
            time.sleep(wait_sec)
            adb.shell("settings put global http_proxy :0")
            capture = recorder.capture()

        ctx = GradingContext.build(
            submission=submission,
            package_dir=package_dir,
            log=logger,
            adb=adb,
            network=capture,
        )
        return self._call(module, ctx)

    @staticmethod
    def _call(module: ModuleType, ctx: GradingContext) -> GradeResult:
        result = module.grade(ctx)
        if not isinstance(result, GradeResult):
            raise GraderLoadError("grade(ctx) did not return a GradeResult")
        return result
