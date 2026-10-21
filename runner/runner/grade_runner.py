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


class _GenericGrader:
    """A grade(ctx) shim backed by a built-in data-driven grader, for authored
    tasks that ship no grade.py of their own."""

    def __init__(self, fn: Any) -> None:
        self.grade = fn


def _load_or_generic(package_dir: Path, success_type: str):
    """Load the task's grade.py, or fall back to a built-in grader keyed by
    success type for authored (UI-created) tasks without one."""
    grade_py = package_dir / "grader" / "grade.py"
    if grade_py.is_file():
        return _load_grader_module(package_dir)
    from runner import graders

    builtin = {"flag": graders.grade_flag, "static_assert": graders.grade_static}.get(success_type)
    if builtin is None:
        raise GraderLoadError(
            f"authored tasks support flag/static_assert only (got {success_type!r}); "
            "device-driven tasks need a code grader in the repo"
        )
    return _GenericGrader(builtin)


def _load_grader_module(package_dir: Path) -> ModuleType:
    grade_py = package_dir / "grader" / "grade.py"
    if not grade_py.is_file():
        raise GraderLoadError(f"no grader at {grade_py}")
    spec = importlib.util.spec_from_file_location(f"masdojo_grader_{package_dir.name}", grade_py)
    if spec is None or spec.loader is None:  # pragma: no cover - defensive
        raise GraderLoadError(f"could not load grader spec for {grade_py}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    if not hasattr(module, "grade"):
        raise GraderLoadError(f"grader {grade_py} does not define grade(ctx)")
    return module


def _read_meta(package_dir: Path) -> dict[str, Any]:
    return yaml.safe_load((package_dir / "task.yaml").read_text(encoding="utf-8")) or {}


class _BundledBackend:
    """Run a task's bundled mock backend (`backend/server.py`) for the duration
    of a network interaction, if one exists. A no-op when absent."""

    def __init__(self, package_dir: Path) -> None:
        self._server = package_dir / "backend" / "server.py"
        self._proc = None

    def __enter__(self) -> "_BundledBackend":
        if self._server.is_file():
            import subprocess
            import sys

            self._proc = subprocess.Popen(
                [sys.executable, str(self._server)],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            logger.info("started bundled mock backend for {}", self._server.parent.parent.name)
            time.sleep(1)  # let it bind before the app calls it
        return self

    def __exit__(self, *exc) -> None:
        if self._proc is not None:
            self._proc.terminate()
            try:
                self._proc.wait(timeout=5)
            except Exception:  # pragma: no cover - cleanup
                self._proc.kill()


class GradeRunner:
    """Orchestrates a single grading job against a (possibly mocked) device."""

    def __init__(self, emulator: Any = None) -> None:
        # `emulator` is an EmulatorManager when a live device is available.
        self._emulator = emulator
        self._seed = ""

    def grade(
        self,
        package_dir: Path,
        submission: dict[str, Any],
        emit: Any = None,
        seed: str = "",
        meta_override: dict[str, Any] | None = None,
        expected_override: dict[str, Any] | None = None,
        apk_override: Path | None = None,
    ) -> GradeResult:
        emit = emit or (lambda *a, **k: None)
        self._seed = seed
        # DB-stored answer key (edited flag / authored task) wins over disk.
        self._expected_override = expected_override
        # Authored tasks carry no on-disk task.yaml; their meta comes from the DB.
        meta = meta_override if meta_override is not None else _read_meta(package_dir)
        success_type = meta.get("success_type", "flag")
        emit(f"loading grader for {package_dir.name} ({success_type})", phase="setup")
        # Authored (UI-created) tasks have no grade.py; grade them with the
        # built-in data-driven grader for their success type.
        module = _load_or_generic(package_dir, success_type)

        adb = self._emulator.adb if self._emulator else None
        live = self._emulator is not None and not config.dry_run

        # A task needs the device only if it's a device-driven success type AND
        # ships a target APK. Comparison/seeded and artifact-based tasks (incl.
        # network_assert tasks graded from committed captures) grade without a
        # device — so a host/attach-mode runner never tries to install a
        # nonexistent APK.
        apk = apk_override if apk_override is not None else package_dir / "app" / "target.apk"
        device_task = (
            success_type in {"frida_assert", "network_assert", "patch_assert"} and apk.is_file()
        )

        if not live or not device_task:
            if not live:
                logger.info("grading {} without a live device", package_dir.name)
            emit("comparing against expected values (no device needed)", phase="grade")
            ctx = GradingContext.build(
                submission=submission,
                package_dir=package_dir,
                log=logger,
                emit=emit,
                seed=seed,
                expected_override=expected_override,
            )
            return self._call(module, ctx)

        # Live device path: restore a clean snapshot and install the target.
        emit("restoring clean AVD snapshot", phase="device")
        self._emulator.restore_snapshot()
        emit(f"adb install {apk.name}", phase="device")
        adb.install(apk, package=meta.get("app_package"))

        if success_type == "network_assert":
            return self._grade_network(module, meta, package_dir, submission, adb, emit)
        return self._grade_device(module, meta, package_dir, submission, adb, emit)

    def _grade_device(self, module, meta, package_dir, submission, adb, emit) -> GradeResult:
        from runner.frida_client import FridaClient

        frida = None
        if meta.get("success_type") == "frida_assert":
            emit("attaching Frida to the target process", phase="frida")
            frida = FridaClient(config.emulator_serial)
        ctx = GradingContext.build(
            submission=submission,
            package_dir=package_dir,
            log=logger,
            adb=adb,
            frida=frida,
            emit=emit,
            seed=self._seed,
            expected_override=getattr(self, "_expected_override", None),
        )
        return self._call(module, ctx)

    def _grade_network(self, module, meta, package_dir, submission, adb, emit) -> GradeResult:
        from runner.network import MitmProxyRecorder

        package = meta.get("app_package")
        activity = meta.get("launch_activity")
        wait_sec = int(meta.get("interaction_wait_sec", 15))
        flow_path = config.artifacts_dir / f"{package_dir.name}.flows"

        emit("starting mitmproxy + bundled mock backend", phase="network")
        with _BundledBackend(package_dir), MitmProxyRecorder(
            config.mitm_port, flow_path
        ) as recorder:
            # Route the device's HTTP(S) traffic through mitmproxy.
            adb.shell(f"settings put global http_proxy 10.0.2.2:{config.mitm_port}")
            if package:
                emit(f"launching {package} through the proxy", phase="network")
                adb.launch_app(package, activity)
            logger.info("network interaction window: {}s", wait_sec)
            emit(f"capturing traffic for {wait_sec}s", phase="network")
            time.sleep(wait_sec)
            adb.shell("settings put global http_proxy :0")
            capture = recorder.capture()
        emit(f"captured {len(capture)} flow(s)", phase="network")

        ctx = GradingContext.build(
            submission=submission,
            package_dir=package_dir,
            log=logger,
            adb=adb,
            network=capture,
            emit=emit,
            seed=self._seed,
            expected_override=getattr(self, "_expected_override", None),
        )
        return self._call(module, ctx)

    @staticmethod
    def _call(module: ModuleType, ctx: GradingContext) -> GradeResult:
        result = module.grade(ctx)
        if not isinstance(result, GradeResult):
            raise GraderLoadError("grade(ctx) did not return a GradeResult")
        return result
