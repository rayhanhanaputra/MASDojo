"""Regression tests for the worker's job-pop resilience.

A blocking BLPOP that idles out raises redis socket TimeoutError; the worker
must treat that (and transient connection errors) as "no job" rather than
crashing the loop.
"""

from __future__ import annotations

import json

import redis.exceptions

from runner.worker import Worker


class _FakeRedis:
    def __init__(self, script):
        self._script = list(script)

    def blpop(self, _key, timeout=5):  # noqa: ANN001, ARG002
        action = self._script.pop(0)
        if isinstance(action, Exception):
            raise action
        return action


def _worker_with(redis_script) -> Worker:
    w = Worker.__new__(Worker)  # bypass __init__ (no real redis/db needed)
    w._redis = _FakeRedis(redis_script)  # type: ignore[attr-defined]
    return w


def test_idle_timeout_returns_none_not_crash():
    w = _worker_with([redis.exceptions.TimeoutError("idle")])
    assert w._pop_job() is None


def test_connection_error_returns_none():
    w = _worker_with([redis.exceptions.ConnectionError("blip")])
    assert w._pop_job() is None


def test_malformed_job_is_dropped():
    w = _worker_with([("masdojo:grading", "{not json")])
    assert w._pop_job() is None


def test_valid_job_is_parsed():
    job = {"job_id": "abc", "submission_id": 7, "task_id": "001", "package_path": "tasks/001"}
    w = _worker_with([("masdojo:grading", json.dumps(job))])
    assert w._pop_job() == job
