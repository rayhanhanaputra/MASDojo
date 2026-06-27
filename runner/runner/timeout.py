"""Hard wall-clock timeout for a grading job using SIGALRM.

The worker runs jobs sequentially in the main thread, so a process-level alarm
is a simple, reliable hard stop. On platforms without SIGALRM the context
manager degrades to a no-op (the worker still relies on per-subprocess timeouts
inside adb/frida calls).
"""

from __future__ import annotations

import signal
from contextlib import contextmanager


class JobTimeout(RuntimeError):
    pass


@contextmanager
def hard_timeout(seconds: int):
    if not hasattr(signal, "SIGALRM"):  # pragma: no cover - non-Unix fallback
        yield
        return

    def _handler(signum, frame):  # noqa: ANN001, ARG001
        raise JobTimeout(f"grading job exceeded {seconds}s hard timeout")

    previous = signal.signal(signal.SIGALRM, _handler)
    signal.alarm(seconds)
    try:
        yield
    finally:
        signal.alarm(0)
        signal.signal(signal.SIGALRM, previous)
