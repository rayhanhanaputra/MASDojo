"""Live grading events: the runner narrates each step so the UI can stream it.

Each grading step is published to a Redis pub/sub channel keyed by submission id
AND appended to a short-lived replay log, so a UI that connects mid-job still
sees the steps that already happened. The backend relays these over SSE into a
live terminal pane — turning a PASS/FAIL from a value that pops out of nowhere
into the visible climax of a real pipeline.
"""

from __future__ import annotations

import json
import time

import redis
from loguru import logger

from runner.config import config

REPLAY_TTL_SEC = 900


def channel(submission_id: int) -> str:
    return f"masdojo:events:{submission_id}"


def replay_key(submission_id: int) -> str:
    return f"masdojo:eventlog:{submission_id}"


class EventPublisher:
    """Publishes grading-step events for one submission. No-ops if Redis is down."""

    def __init__(self, submission_id: int) -> None:
        self.sid = submission_id
        self._channel = channel(submission_id)
        self._replay = replay_key(submission_id)
        try:
            # Bounded timeouts so a black-holed Redis can never stall the
            # grading thread on emit().
            self._redis: redis.Redis | None = redis.Redis.from_url(
                config.redis_url,
                decode_responses=True,
                socket_connect_timeout=1,
                socket_timeout=1,
            )
        except Exception as exc:  # noqa: BLE001 - never let telemetry break grading
            logger.warning("event publisher disabled (redis error): {}", exc)
            self._redis = None

    def emit(self, msg: str, *, level: str = "info", phase: str = "") -> None:
        event = {"ts": time.time(), "level": level, "phase": phase, "msg": msg}
        data = json.dumps(event)
        logger.debug("event[{}] {}", self.sid, msg)
        if self._redis is None:
            return
        try:
            # One round-trip for publish + replay-append + TTL.
            (
                self._redis.pipeline()
                .publish(self._channel, data)
                .rpush(self._replay, data)
                .expire(self._replay, REPLAY_TTL_SEC)
                .execute()
            )
        except Exception as exc:  # noqa: BLE001
            # Disable after the first failure so we don't retry-stall every step.
            logger.debug("event publish failed, disabling publisher: {}", exc)
            self._redis = None

    def done(self, status: str) -> None:
        """Terminal marker so the stream can close cleanly."""
        self.emit(f"verdict: {status.upper()}", level="done", phase="done")
