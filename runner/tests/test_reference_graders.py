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


# ── 009 frida_assert (behavioral / proof-of-technique) ────────────────────────
_NOOP = "Java.perform(function(){});"
_HOOK = (
    'Java.perform(function(){'
    'var C=Java.use("org.masdojo.vaultguard.RootChecker");'
    'C.isDeviceRooted.implementation=function(){ return false; };});'
)


class _FakeSession:
    def __init__(self, payloads):
        self._payloads = payloads

    def wait(self, _seconds):  # noqa: ANN001
        pass

    def payloads(self):
        return self._payloads

    def unload(self):
        pass


class _FakeEmu:
    """Implements both the adb and frida facets. Serves the baseline logcat for
    the no-op run and the hooked logcat for the learner's script, so the
    behavioral grader's two-run baseline→hook delta can be exercised without KVM.
    """

    def __init__(self, baseline_log: str, hooked_log: str):
        self.baseline_log = baseline_log
        self.hooked_log = hooked_log
        self._last_was_noop = True

    # adb facet
    def clear_logcat(self):
        pass

    def logcat_dump(self, since=None):  # noqa: ANN001
        return self.baseline_log if self._last_was_noop else self.hooked_log

    # frida facet
    def spawn_and_inject(self, package, script):  # noqa: ANN001
        self._last_was_noop = script.strip() == _NOOP
        return _FakeSession([] if self._last_was_noop else ["hooked"]), 4242


def _grade009(submission, baseline_log, hooked_log):
    task = TASKS / "009-root-detection-bypass"
    grade = _load_grader(task).grade
    emu = _FakeEmu(baseline_log, hooked_log)
    return grade(
        GradingContext.build(
            submission=submission, package_dir=task, log=logger, adb=emu, frida=emu
        )
    )


def test_task009_behavioral_pass():
    flag = "FLAG{r00t_ch3ck_bypass3d}"
    # Locked at baseline, unlocked after the hook -> attributable pass.
    ok = _grade009(
        {"script": _HOOK},
        baseline_log="W VaultGuard: MASDOJO_DENIED: rooted device detected\n",
        hooked_log=f"I VaultGuard: MASDOJO_UNLOCK:{flag}\n",
    )
    assert ok.passed is True
    # The verdict ships a structured evidence bundle (baseline log, hooked log,
    # trace, timeline).
    labels = {e.label for e in ok.evidence_items}
    assert "baseline logcat (no hook)" in labels
    assert "logcat after your hook" in labels
    assert "timeline" in labels


def test_task009_hook_did_not_bypass_fails():
    denied = "W VaultGuard: MASDOJO_DENIED: rooted device detected\n"
    bad = _grade009({"script": _HOOK}, baseline_log=denied, hooked_log=denied)
    assert bad.passed is False


def test_task009_non_gating_environment_cannot_false_pass():
    """The novel guarantee: if the app wasn't gating at baseline, the unlock
    can't be attributed to the learner's hook, so it must FAIL even though the
    unlock marker is present in the hooked run."""
    flag = "FLAG{r00t_ch3ck_bypass3d}"
    already_unlocked = f"I VaultGuard: MASDOJO_UNLOCK:{flag}\n"
    bad = _grade009(
        {"script": _HOOK},
        baseline_log=already_unlocked,  # app never gated
        hooked_log=already_unlocked,
    )
    assert bad.passed is False
    assert not bad.checks[0].passed  # the baseline-gating check is what fails


def test_task009_empty_script_fails_fast():
    empty = _grade009({"script": ""}, baseline_log="", hooked_log="")
    assert empty.passed is False


def test_task009_dry_run_static_fallback():
    """With no device (NullDevice facets) the grader statically validates the
    script so the task stays solvable for self-study."""
    task = TASKS / "009-root-detection-bypass"
    grade = _load_grader(task).grade

    ok = grade(GradingContext.build(submission={"script": _HOOK}, package_dir=task, log=logger))
    assert ok.passed is True

    bad = grade(GradingContext.build(submission={"script": _NOOP}, package_dir=task, log=logger))
    assert bad.passed is False
