"""Per-session device allocation for the hosted interactive lab.

This is the seam for a future KVM device pool. When an admin enables
`lab_allow_device_hosted`, a hosted lab session asks the pool for a device; the
pool returns a binding describing which device the session may reach and over
WHICH dedicated docker network (so a learner reaches only their own emulator,
never the host bridge / DB / Redis / backend / other learners).

Until a pool is provisioned, `allocate` returns None: the session gets no device
(static-analysis only). Enabling the admin flag is therefore safe today - it
simply has nothing to allocate, and we never fall back to an exposed bridge.
"""

from __future__ import annotations

from dataclasses import dataclass

from loguru import logger


@dataclass(frozen=True)
class DeviceBinding:
    """A device allocated to one session.

    serial:      adb serial to target (e.g. "emulator-5554").
    adb_socket:  value for the container's ADB_SERVER_SOCKET (reaches only this
                 device's adb endpoint, not a shared all-devices server).
    network:     name of the dedicated docker network connecting the session
                 container to its emulator (NOT the host bridge).
    """

    serial: str
    adb_socket: str
    network: str


def allocate(session_id: int, user_id: int) -> DeviceBinding | None:
    """Allocate a device for a hosted session, or None if none is available.

    No pool is provisioned yet, so this always returns None. A real
    implementation (KVM host) would boot/lease an emulator, attach it to a
    per-session network, and return the binding here; teardown would release it
    in `release`.
    """
    logger.info(
        "device pool: no device available for session {} (user {}); static analysis only",
        session_id,
        user_id,
    )
    return None


def release(session_id: int) -> None:
    """Release a session's device back to the pool. No-op until a pool exists."""
    return None
