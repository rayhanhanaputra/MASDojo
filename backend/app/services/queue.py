"""Redis grading-job queue producer.

The backend enqueues a grading job; the runner (a separate process/container)
consumes it. We keep the contract tiny and explicit: a JSON document on a Redis
list. The runner writes results straight back to Postgres, so the backend only
needs the producer side here.
"""

from __future__ import annotations

import json
import uuid

import redis
from loguru import logger

from app.core.config import settings

_client: redis.Redis | None = None


def get_redis() -> redis.Redis:
    global _client
    if _client is None:
        _client = redis.Redis.from_url(settings.redis_url, decode_responses=True)
    return _client


def enqueue_grading_job(submission_id: int, task_id: str, package_path: str) -> str:
    """Push a grading job and return its id."""
    job_id = uuid.uuid4().hex
    job = {
        "job_id": job_id,
        "submission_id": submission_id,
        "task_id": task_id,
        "package_path": package_path,
        "timeout_sec": settings.grading_job_timeout_sec,
    }
    client = get_redis()
    client.rpush(settings.grading_queue, json.dumps(job))
    logger.info("enqueued grading job {} for submission {}", job_id, submission_id)
    return job_id
