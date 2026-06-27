"""PASS/FAIL round-trip tests for the three reference-task graders.

The live emulator path needs KVM, so here we drive each real grader
(`tasks/*/grader/grade.py`) with a GradingContext whose device facets are
faithful fakes. This proves the grading logic for every success type:
static_assert (001), network_assert (005), and frida_assert (009).
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

from loguru import logger

from runner.grader_api import GradingContext
from runner.network import Flow, NetworkCapture

REPO_ROOT = Path(__file__).resolve().parents[2]
TASKS = REPO_ROOT / "tasks"


def _load_grader(task_dir: Path):
    spec = importlib.util.spec_from_file_location(
        f"grader_{task_dir.name}", task_dir / "grader" / "grade.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


# ── 001 static_assert ─────────────────────────────────────────────────────────
def test_task001_static_pass_and_fail():
    task = TASKS / "001-find-hardcoded-secret"
    grade = _load_grader(task).grade
    secret = "msd_live_sk_8f3c1d77a94b42e0b6c5e9f0a1d2c3b4"

    ok = grade(GradingContext.build(submission={"value": secret}, package_dir=task, log=logger))
    assert ok.passed is True
    assert ok.checks[0].passed is True

    bad = grade(
        GradingContext.build(submission={"value": "msd_live_sk_wrong"}, package_dir=task, log=logger)
    )
    assert bad.passed is False


# ── 005 network_assert ────────────────────────────────────────────────────────
def _telemetry_capture(token: str) -> NetworkCapture:
    return NetworkCapture(
        [
            Flow(
                method="POST",
                url="http://10.0.2.2:8090/api/v1/telemetry",
                host="10.0.2.2",
                path="/api/v1/telemetry",
                request_body=f"device_id=pulse-emulator&device_token={token}",
            )
        ]
    )


def test_task005_network_pass_and_fail():
    task = TASKS / "005-intercept-api-call"
    grade = _load_grader(task).grade
    token = "FLAG{n3tw0rk_1nt3rc3pt3d}"

    ok = grade(
        GradingContext.build(
            submission={"value": token},
            package_dir=task,
            log=logger,
            network=_telemetry_capture(token),
        )
    )
    assert ok.passed is True
    assert all(c.passed for c in ok.checks)

    # No traffic captured -> fail (learner never intercepted anything).
    empty = grade(
        GradingContext.build(
            submission={"value": token},
            package_dir=task,
            log=logger,
            network=NetworkCapture([]),
        )
    )
    assert empty.passed is False

    # Captured the request but submitted the wrong value -> fail.
    wrong = grade(
        GradingContext.build(
            submission={"value": "FLAG{guessed}"},
            package_dir=task,
            log=logger,
            network=_telemetry_capture(token),
        )
    )
    assert wrong.passed is False


# ── 009 frida_assert ──────────────────────────────────────────────────────────
class _FakeSession:
    def wait(self, _seconds):  # noqa: ANN001
        pass

    def unload(self):
        pass


class _FakeFrida:
    def __init__(self, script_loads: bool = True):
        self.script_loads = script_loads
        self.injected = None

    def spawn_and_inject(self, package, script):  # noqa: ANN001
        self.injected = (package, script)
        return _FakeSession(), 4242


class _FakeAdb:
    def __init__(self, logcat: str):
        self._logcat = logcat
        self.cleared = False

    def clear_logcat(self):
        self.cleared = True

    def logcat_dump(self, since=None):  # noqa: ANN001
        return self._logcat


def test_task009_frida_pass_and_fail():
    task = TASKS / "009-root-detection-bypass"
    grade = _load_grader(task).grade
    flag = "FLAG{r00t_ch3ck_bypass3d}"
    script = "Java.perform(function(){})"

    # Hook flipped the check -> app logged the unlock marker -> pass.
    unlocked_log = f"I VaultGuard: MASDOJO_UNLOCK:{flag}\n"
    ok = grade(
        GradingContext.build(
            submission={"script": script},
            package_dir=task,
            log=logger,
            adb=_FakeAdb(unlocked_log),
            frida=_FakeFrida(),
        )
    )
    assert ok.passed is True

    # App still treated the device as rooted -> denied marker -> fail.
    denied_log = "W VaultGuard: MASDOJO_DENIED: rooted device detected, vault locked\n"
    denied = grade(
        GradingContext.build(
            submission={"script": script},
            package_dir=task,
            log=logger,
            adb=_FakeAdb(denied_log),
            frida=_FakeFrida(),
        )
    )
    assert denied.passed is False

    # No script submitted -> fail fast.
    empty = grade(
        GradingContext.build(
            submission={"script": ""},
            package_dir=task,
            log=logger,
            adb=_FakeAdb(unlocked_log),
            frida=_FakeFrida(),
        )
    )
    assert empty.passed is False
