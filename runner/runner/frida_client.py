"""Frida instrumentation helper for frida_assert graders.

Wraps the `frida` Python bindings to spawn or attach to the target process,
inject a learner-supplied or grader-supplied script, and collect messages the
script sends back via `send(...)`. Hook signals are surfaced as structured
messages the grader can assert on.
"""

from __future__ import annotations

import threading
import time
from typing import Any

from loguru import logger

try:  # frida is a heavy native dep; keep import soft so unit tests can run.
    import frida
except Exception:  # pragma: no cover - environment without frida
    frida = None  # type: ignore[assignment]


class FridaError(RuntimeError):
    pass


class FridaSession:
    """A live instrumentation session over one injected script."""

    def __init__(self, session: Any, script: Any) -> None:
        self._session = session
        self._script = script
        self._messages: list[dict[str, Any]] = []
        self._lock = threading.Lock()
        script.on("message", self._on_message)

    def _on_message(self, message: dict[str, Any], data: Any) -> None:
        with self._lock:
            self._messages.append(message)
        logger.debug("frida message: {}", message)

    @property
    def messages(self) -> list[dict[str, Any]]:
        with self._lock:
            return list(self._messages)

    def payloads(self) -> list[Any]:
        """Return the `payload` of every send() message from the script."""
        return [m.get("payload") for m in self.messages if m.get("type") == "send"]

    def received(self, predicate) -> bool:
        """True if any script payload satisfies `predicate`."""
        return any(predicate(p) for p in self.payloads())

    def wait(self, seconds: float) -> None:
        time.sleep(seconds)

    def unload(self) -> None:
        try:
            self._script.unload()
            self._session.detach()
        except Exception:  # pragma: no cover - best-effort teardown
            pass


class FridaClient:
    """Attach to / spawn the target app and inject scripts."""

    def __init__(self, serial: str) -> None:
        if frida is None:  # pragma: no cover - guarded at runtime
            raise FridaError("frida bindings are not installed in this environment")
        self._serial = serial
        self._device = frida.get_device(serial, timeout=30)

    def spawn_and_inject(self, package: str, script_source: str) -> tuple[FridaSession, int]:
        """Spawn the package paused, inject the script, then resume.

        Returns the session and the spawned pid. Spawning (rather than attaching)
        lets a script hook code that runs early in process startup — essential
        for root-detection and anti-tamper checks.
        """
        pid = self._device.spawn([package])
        session = self._device.attach(pid)
        script = session.create_script(script_source)
        wrapper = FridaSession(session, script)
        script.load()
        self._device.resume(pid)
        logger.info("frida injected into {} (pid {})", package, pid)
        return wrapper, pid

    def attach_and_inject(self, target: str | int, script_source: str) -> FridaSession:
        """Attach to a running process (by name or pid) and inject a script."""
        session = self._device.attach(target)
        script = session.create_script(script_source)
        wrapper = FridaSession(session, script)
        script.load()
        return wrapper
