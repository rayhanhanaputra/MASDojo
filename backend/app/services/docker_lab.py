"""Per-session isolated lab containers (hosted-safe).

Each lab session gets its own ephemeral, resource-constrained container spun up
from the lab image. Learners can't read each other's files, see each other's
processes, persist anything, escalate privileges, exhaust the host, or (by
default in hosted mode) reach any network/device. The backend drives this via
the mounted docker socket; the learner only ever gets an `exec` shell inside
their own throwaway container.

Solo mode keeps the simpler single shared-container path (one trusted operator
on their own machine) and does not use this module.
"""

from __future__ import annotations

import re
import subprocess

from loguru import logger

from app.core.config import settings

_NAME_RE = re.compile(r"^[a-zA-Z0-9_.-]{1,120}$")
_SESSION_LABEL = "masdojo.lab-session"
_DOCKER_TIMEOUT = 15


def session_container_name(session_id: int) -> str:
    name = f"masdojo-lab-session-{int(session_id)}"
    if not _NAME_RE.match(name):  # defensive; int() already guarantees it
        raise ValueError("invalid session id")
    return name


def _run(args: list[str], timeout: int = _DOCKER_TIMEOUT) -> subprocess.CompletedProcess | None:
    try:
        return subprocess.run(args, capture_output=True, text=True, timeout=timeout, check=False)
    except (OSError, subprocess.SubprocessError) as exc:
        logger.warning("docker call failed ({}): {}", args[:3], exc)
        return None


_UNSAFE_REPO_DIRS = {
    "/",
    "/root",
    "/etc",
    "/home",
    "/var",
    "/usr",
    "/bin",
    "/boot",
    "/sys",
    "/proc",
}


def _safe_host_repo_dir(path: str) -> bool:
    """Only mount the committed targets from a plausible repo dir: an absolute
    path that isn't a sensitive system root. Guards against a misconfigured
    HOST_REPO_DIR exposing host files (even read-only) to every learner."""
    if not path or not path.startswith("/"):
        return False
    normalized = "/" + path.strip("/")
    if normalized in _UNSAFE_REPO_DIRS:
        return False
    return True


def is_running(name: str) -> bool:
    out = _run(["docker", "inspect", "-f", "{{.State.Running}}", name], timeout=5)
    return bool(out and out.returncode == 0 and out.stdout.strip() == "true")


def ensure_session_container(
    session_id: int, network: str = "none", adb_socket: str | None = None
) -> str | None:
    """Create (or reuse) the hardened per-session container; return its name.

    `network` is the docker network the container joins; it defaults to "none"
    (fully isolated, static analysis). A device-bound session passes the device
    pool's DEDICATED network name (never the host bridge), plus `adb_socket`
    pointing only at that device. Returns None if the container can't be created
    (caller degrades gracefully)."""
    name = session_container_name(session_id)
    if is_running(name):
        return name

    # A fresh container may be left over (stopped) under the same name; clear it.
    _run(["docker", "rm", "-f", name], timeout=10)

    net = network if network else "none"
    args = [
        "docker",
        "run",
        "--detach",
        "--rm",
        "--name",
        name,
        f"--label={_SESSION_LABEL}={int(session_id)}",
        # Identity + privilege containment.
        "--user",
        "labuser:labuser",
        "--cap-drop",
        "ALL",
        "--security-opt",
        "no-new-privileges",
        # Resource caps so one learner can't DoS the host.
        f"--memory={settings.lab_mem_limit}",
        f"--memory-swap={settings.lab_mem_limit}",
        f"--cpus={settings.lab_cpu_limit}",
        f"--pids-limit={settings.lab_pids_limit}",
        "--ulimit",
        "nofile=2048:4096",
        "--ulimit",
        "fsize=5368709120",  # 5 GiB max file
        # Read-only root; writable scratch is tmpfs (wiped with the container).
        # tmpfs mounts default to root-owned, so set uid/gid to labuser (1000)
        # or the unprivileged user couldn't write to its own workspace.
        "--read-only",
        "--tmpfs",
        "/work:rw,nosuid,nodev,size=2g,uid=1000,gid=1000,mode=0700",
        "--tmpfs",
        "/tmp:rw,nosuid,nodev,size=1g,uid=1000,gid=1000,mode=1777",
        "--tmpfs",
        "/home/labuser:rw,nosuid,nodev,size=1g,uid=1000,gid=1000,mode=0700",
        # Network: "none" (static analysis) by default; a device-bound session
        # joins the pool's dedicated network, NEVER the host bridge.
        "--network",
        net,
    ]
    # Target materials, read-only. Paths are resolved on the HOST (the daemon
    # interprets -v source paths host-side, not inside the backend container),
    # so we use the host repo dir (passed in via HOST_REPO_DIR) and the task
    # store's docker volume name.
    if _safe_host_repo_dir(settings.host_repo_dir):
        base = settings.host_repo_dir.rstrip("/")
        args += ["-v", f"{base}/apps/vaultbank:/targets/app:ro"]
        args += ["-v", f"{base}/tasks:/targets/tasks:ro"]
    if settings.lab_task_store_volume:
        args += ["-v", f"{settings.lab_task_store_volume}:/targets/task-store:ro"]
    if adb_socket:
        # The pool's adb endpoint reaches ONLY this session's device (it lives on
        # the dedicated network above); no host-gateway, no shared adb server.
        args += ["--env", f"ADB_SERVER_SOCKET={adb_socket}"]
    args += [settings.lab_image, "sleep", "infinity"]

    out = _run(args, timeout=20)
    if not out or out.returncode != 0:
        logger.error(
            "could not start lab session container {}: {}",
            name,
            (out.stderr.strip() if out else "docker unavailable"),
        )
        return None
    logger.info("lab session container up: {} (network={})", name, net)
    return name


def remove_session_container(session_id: int) -> None:
    name = session_container_name(session_id)
    _run(["docker", "rm", "-f", name], timeout=10)


def reap_orphans(active_session_ids: set[int]) -> int:
    """Remove any masdojo-lab-session-* containers whose session is no longer
    active (e.g. left over after a backend restart). Returns how many removed."""
    out = _run(["docker", "ps", "-aq", "--filter", f"label={_SESSION_LABEL}"], timeout=10)
    if not out or out.returncode != 0 or not out.stdout.strip():
        return 0
    removed = 0
    for cid in out.stdout.split():
        label = _run(
            ["docker", "inspect", "-f", f'{{{{index .Config.Labels "{_SESSION_LABEL}"}}}}', cid],
            timeout=5,
        )
        if not label or label.returncode != 0:
            continue
        try:
            sid = int(label.stdout.strip())
        except ValueError:
            continue
        if sid not in active_session_ids:
            _run(["docker", "rm", "-f", cid], timeout=10)
            removed += 1
    if removed:
        logger.info("reaped {} orphaned lab container(s)", removed)
    return removed
