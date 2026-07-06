"""Attach mode: the runner grades against a participant-owned AVD without
booting, snapshotting, or shutting it down. Verifies the lifecycle no-ops that
make the local single-participant model safe (the actual attach/boot needs a
device and is exercised on the participant's host)."""

from __future__ import annotations

from pathlib import Path

from runner.avd import EmulatorManager


def _mgr() -> EmulatorManager:
    return EmulatorManager(avd_name="masdojo_avd", sdk_root=Path("/opt/android-sdk"), serial="emulator-5554")


def test_snapshot_ops_are_noops_when_attached(monkeypatch):
    mgr = _mgr()
    mgr._attached = True

    called = {"console": False}
    monkeypatch.setattr(mgr, "_emu_console", lambda *_a, **_k: called.__setitem__("console", True))

    # In attach mode these must NOT touch the participant's device.
    mgr.restore_snapshot()
    mgr.save_snapshot()
    mgr.shutdown()
    assert called["console"] is False
    assert mgr.attached is True


def test_snapshot_restore_runs_when_not_attached(monkeypatch):
    mgr = _mgr()
    calls = []
    monkeypatch.setattr(mgr, "_emu_console", lambda cmd: calls.append(cmd))

    mgr.restore_snapshot()
    mgr.save_snapshot()
    assert any("snapshot load" in c for c in calls)
    assert any("snapshot save" in c for c in calls)
