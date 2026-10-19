"""Per-session device allocation for the hosted interactive lab.

When an admin enables `lab_allow_device_hosted`, a hosted lab session asks the
pool for a device. The pool boots a per-session emulator CONTAINER on a per-
session, **internal** docker network (no host bridge, no internet, no other
services), and the session's lab container joins that same network - so a
learner reaches ONLY their own emulator and nothing else on the host.

Safety invariants (keep these if you change this file):
  * A binding is returned ONLY when a real, isolated device is up. On ANY failure
    we clean up and return None, so the caller falls back to static-analysis.
  * The returned `network` is a dedicated per-session network, NEVER the host
    bridge; `adb_socket` reaches only that session's emulator.
  * EMPTY `lab_emulator_image` => pool disabled => always None (safe default).

STATUS: this needs a KVM host to run and verify (the emulator image needs
/dev/kvm). It is a working skeleton: adjust `lab_emulator_image` and the adb
exposure to match your chosen emulator image (e.g. budtmo/docker-android or
google/android-emulator-container-scripts), then verify on the KVM host.
"""

from __future__ import annotations

import subprocess
from dataclasses import dataclass

from loguru import logger
from sqlalchemy.orm import Session

from app.services import instance_config

_NET_PREFIX = "masdojo-lab-net-"
_EMU_PREFIX = "masdojo-lab-emu-"
_LABEL = "masdojo.lab-session"


@dataclass(frozen=True)
class DeviceBinding:
    """A device allocated to one session.

    serial:      adb serial to target (e.g. "emulator-5554").
    adb_socket:  value for the container's ADB_SERVER_SOCKET - reaches only this
                 session's emulator (over the dedicated network), not a shared
                 all-devices adb server.
    network:     name of the dedicated docker network the session container must
                 join (NOT the host bridge).
    """

    serial: str
    adb_socket: str
    network: str


def _run(args: list[str], timeout: int = 20) -> subprocess.CompletedProcess | None:
    try:
        return subprocess.run(args, capture_output=True, text=True, timeout=timeout, check=False)
    except (OSError, subprocess.SubprocessError) as exc:
        logger.warning("device-pool docker call failed ({}): {}", args[:3], exc)
        return None


def _net_name(session_id: int) -> str:
    return f"{_NET_PREFIX}{int(session_id)}"


def _emu_name(session_id: int) -> str:
    return f"{_EMU_PREFIX}{int(session_id)}"


def allocate(session_id: int, user_id: int, db: Session) -> DeviceBinding | None:
    """Boot a per-session emulator on a dedicated internal network and return a
    binding, or None if no device can be safely provisioned. Pool config
    (image / adb port / serial / boot timeout) comes from the admin-managed
    instance settings in the DB, not env."""
    cfg = instance_config.get_config(db)
    if not cfg.lab_emulator_image:
        logger.info(
            "device pool: no emulator image configured; session {} stays static", session_id
        )
        return None

    net = _net_name(session_id)
    emu = _emu_name(session_id)
    sid = int(session_id)

    # Clean any leftovers from a crashed previous attempt with this id.
    release(session_id)

    # 1) Dedicated, INTERNAL network: the session + emulator can talk to each
    #    other but to nothing else (no host bridge, no internet, no DB/Redis).
    net_out = _run(["docker", "network", "create", "--internal", "--label", f"{_LABEL}={sid}", net])
    if not net_out or net_out.returncode != 0:
        logger.error("device pool: could not create network {}", net)
        return None

    # 2) Per-session emulator container on that network. Needs /dev/kvm on the
    #    host. The image must run an adb server on lab_emulator_adb_port reachable
    #    over the network (adjust the image/args to your chosen emulator image).
    emu_out = _run(
        [
            "docker",
            "run",
            "--detach",
            "--rm",
            "--name",
            emu,
            "--label",
            f"{_LABEL}={sid}",
            "--network",
            net,
            "--device",
            "/dev/kvm",
            "--shm-size",
            "2g",
            cfg.lab_emulator_image,
        ],
        timeout=60,
    )
    if not emu_out or emu_out.returncode != 0:
        logger.error(
            "device pool: could not start emulator {} ({})",
            emu,
            (emu_out.stderr.strip() if emu_out else "docker unavailable"),
        )
        release(session_id)
        return None

    # 3) Wait for the emulator's adb server + device to be ready.
    if not _wait_for_device(emu, cfg.lab_emulator_boot_timeout_sec):
        logger.error("device pool: emulator {} did not become ready; releasing", emu)
        release(session_id)
        return None

    logger.info("device pool: session {} bound to {} on {}", session_id, emu, net)
    return DeviceBinding(
        serial=cfg.lab_emulator_serial,
        # The emulator container's adb server, reachable only on `net` by its name.
        adb_socket=f"tcp:{emu}:{cfg.lab_emulator_adb_port}",
        network=net,
    )


def _wait_for_device(emu: str, deadline: int) -> bool:
    """Poll the emulator container until adb reports a booted device, bounded by
    the boot timeout. Returns False on timeout/error."""
    import time

    waited = 0
    step = 5
    while waited < deadline:
        out = _run(
            ["docker", "exec", emu, "adb", "shell", "getprop", "sys.boot_completed"], timeout=10
        )
        if out and out.returncode == 0 and out.stdout.strip() == "1":
            return True
        time.sleep(step)
        waited += step
    return False


def release(session_id: int) -> None:
    """Tear down a session's emulator and network. Safe to call repeatedly."""
    _run(["docker", "rm", "-f", _emu_name(session_id)], timeout=15)
    _run(["docker", "network", "rm", _net_name(session_id)], timeout=15)


def reap_orphans(active_session_ids: set[int]) -> int:
    """Remove emulator containers + networks with no active session (startup
    cleanup). Mirrors docker_lab.reap_orphans. Returns how many emulators removed."""
    out = _run(["docker", "ps", "-aq", "--filter", f"label={_LABEL}"], timeout=10)
    removed = 0
    if out and out.returncode == 0 and out.stdout.strip():
        for cid in out.stdout.split():
            label = _run(
                ["docker", "inspect", "-f", f'{{{{index .Config.Labels "{_LABEL}"}}}}', cid],
                timeout=5,
            )
            try:
                sid = int(label.stdout.strip()) if label and label.returncode == 0 else None
            except ValueError:
                sid = None
            if sid is not None and sid not in active_session_ids:
                _run(["docker", "rm", "-f", cid], timeout=15)
                removed += 1
    # Prune orphaned networks too.
    nets = _run(["docker", "network", "ls", "-q", "--filter", f"label={_LABEL}"], timeout=10)
    if nets and nets.returncode == 0:
        for nid in nets.stdout.split():
            label = _run(
                ["docker", "network", "inspect", "-f", f'{{{{index .Labels "{_LABEL}"}}}}', nid],
                timeout=5,
            )
            try:
                sid = int(label.stdout.strip()) if label and label.returncode == 0 else None
            except ValueError:
                sid = None
            if sid is not None and sid not in active_session_ids:
                _run(["docker", "network", "rm", nid], timeout=15)
    return removed
