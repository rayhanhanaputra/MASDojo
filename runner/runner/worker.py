"""Grading worker: consume jobs from Redis and grade them on the AVD.

Lifecycle:
  1. (live mode) boot the AVD once and snapshot a clean state.
  2. BLPOP a job from the grading queue.
  3. Mark the submission running, resolve its task package.
  4. Grade under a hard wall-clock timeout, restoring the clean snapshot first.
  5. Persist the GradeResult (or an error) back to Postgres.
  6. Repeat.

Each job is isolated by snapshot restore; failures in one job never leak into
the next.
"""

from __future__ import annotations

import json
import signal as _signal
import sys
import time
from pathlib import Path
from typing import Any

import redis
import redis.exceptions
from loguru import logger

from runner.config import config
from runner.grade_runner import GradeRunner
from runner.results import ResultWriter
from runner.timeout import JobTimeout, hard_timeout


class Worker:
    def __init__(self) -> None:
        self._redis = redis.Redis.from_url(config.redis_url, decode_responses=True)
        self._results = ResultWriter()
        self._emulator = None
        self._runner = GradeRunner(emulator=None)
        self._running = True

    # ── device lifecycle ──────────────────────────────────────────────────
    def _start_device(self) -> None:
        if config.dry_run:
            logger.warning("RUNNER_DRY_RUN set: grading without a live emulator")
            return
        from runner.avd import EmulatorManager

        self._emulator = EmulatorManager(
            avd_name=config.avd_name,
            sdk_root=config.android_sdk_root,
            serial=config.emulator_serial,
        )
        try:
            self._emulator.boot(cold=True)
            self._emulator.start_frida_server()
            self._emulator.install_mitm_ca()
            self._emulator.save_snapshot()
        except Exception as exc:  # noqa: BLE001
            logger.exception("failed to boot AVD; falling back to dry-run: {}", exc)
            self._emulator = None
        self._runner = GradeRunner(emulator=self._emulator)

    def _stop_device(self) -> None:
        if self._emulator is not None:
            self._emulator.shutdown()

    # ── package resolution ────────────────────────────────────────────────
    def _resolve_package(self, package_path: str) -> Path:
        candidates = [
            config.tasks_root.parent / package_path,
            config.tasks_root / Path(package_path).name,
            Path(package_path),
        ]
        for candidate in candidates:
            if (candidate / "task.yaml").is_file():
                return candidate
        raise FileNotFoundError(f"task package not found for '{package_path}'")

    # ── job handling ──────────────────────────────────────────────────────
    def _handle(self, job: dict[str, Any]) -> None:
        from runner.events import EventPublisher

        submission_id = job["submission_id"]
        task_id = job["task_id"]
        timeout = int(job.get("timeout_sec", config.job_timeout_sec))
        events = EventPublisher(submission_id)
        events.emit(f"job picked up for {task_id}", phase="queue")
        self._results.mark_running(submission_id)
        try:
            package_dir = self._resolve_package(job["package_path"])
            submission = self._fetch_submission_payload(submission_id)
            with hard_timeout(timeout):
                result = self._runner.grade(package_dir, submission, emit=events.emit)
            for check in result.checks:
                events.emit(
                    f"{'PASS' if check.passed else 'FAIL'} · {check.name}"
                    + (f" — {check.detail}" if check.detail else ""),
                    level="check",
                    phase="grade",
                )
            self._results.record_result(submission_id, task_id, result)
            events.done("passed" if result.passed else "failed")
        except JobTimeout as exc:
            self._results.record_error(submission_id, str(exc))
            events.emit(str(exc), level="error", phase="error")
            events.done("error")
        except Exception as exc:  # noqa: BLE001 - never let one job kill the loop
            logger.exception("grading job {} failed", submission_id)
            self._results.record_error(submission_id, f"{type(exc).__name__}: {exc}")
            events.emit(f"{type(exc).__name__}: {exc}", level="error", phase="error")
            events.done("error")

    def _fetch_submission_payload(self, submission_id: int) -> dict[str, Any]:
        from sqlalchemy import create_engine, text

        engine = create_engine(config.database_url, future=True)
        with engine.connect() as conn:
            row = conn.execute(
                text("SELECT payload FROM submissions WHERE id=:id"),
                {"id": submission_id},
            ).scalar()
        if row is None:
            return {}
        return row if isinstance(row, dict) else json.loads(row)

    # ── main loop ─────────────────────────────────────────────────────────
    def run(self) -> None:
        self._install_signal_handlers()
        logger.info("MASDojo runner starting; queue='{}'", config.grading_queue)
        self._start_device()
        try:
            while self._running:
                job = self._pop_job()
                if job is None:
                    continue
                logger.info("picked up job {} (submission {})", job.get("job_id"), job.get("submission_id"))
                self._handle(job)
        finally:
            self._stop_device()
            logger.info("runner stopped")

    def _pop_job(self) -> dict[str, Any] | None:
        """Block for the next job, tolerating idle timeouts and blips.

        redis-py's blocking BLPOP raises a socket TimeoutError when the server
        timeout elapses on an empty queue; that's normal idling, not a failure,
        and must not kill the worker loop.
        """
        try:
            item = self._redis.blpop(config.grading_queue, timeout=5)
        except redis.exceptions.TimeoutError:
            return None
        except redis.exceptions.ConnectionError as exc:
            logger.warning("redis connection issue, retrying: {}", exc)
            time.sleep(1)
            return None
        if item is None:
            return None
        _, raw = item
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            logger.error("dropping malformed job: {}", raw)
            return None

    def _install_signal_handlers(self) -> None:
        def _stop(signum, frame):  # noqa: ANN001, ARG001
            logger.info("received signal {}, finishing current job then exiting", signum)
            self._running = False

        for sig in (_signal.SIGINT, _signal.SIGTERM):
            _signal.signal(sig, _stop)


def main() -> int:
    from runner.logging_setup import configure_logging

    configure_logging()
    Worker().run()
    return 0


if __name__ == "__main__":
    sys.exit(main())
