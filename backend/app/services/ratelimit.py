"""Per-user rate limiting for credit-spending endpoints (the AI mentor).

A fixed-window counter in Redis: the first call in a window sets a TTL, and
calls beyond the limit are rejected until the window expires. Kept deliberately
simple — the goal is to stop a single learner from burning their (or a shared
cohort) BYOK budget, not to be a precise distributed limiter.
"""

from __future__ import annotations

from fastapi import HTTPException, status
from loguru import logger

from app.core.config import settings
from app.services.queue import get_redis


def enforce_mentor_rate_limit(user_id: int) -> None:
    """Raise 429 if the user has exceeded the hourly mentor-call budget."""
    limit = settings.mentor_rate_limit_per_hour
    if limit <= 0:
        return
    key = f"masdojo:mentor:rl:{user_id}"
    try:
        client = get_redis()
        count = client.incr(key)
        if count == 1:
            client.expire(key, 3600)
    except Exception as exc:  # noqa: BLE001 - never let limiter outage block usage
        logger.warning("mentor rate-limit check skipped (redis error): {}", exc)
        return
    if count > limit:
        raise HTTPException(
            status.HTTP_429_TOO_MANY_REQUESTS,
            f"AI mentor limit reached ({limit}/hour). Try again later.",
        )
