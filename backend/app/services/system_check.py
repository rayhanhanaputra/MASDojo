"""System health checks for the admin dashboard.

Reports whether each moving part is up: database, Redis (the grading queue
backend), the grading runner and its emulator (via the runner's heartbeat in
Redis), the interactive lab, and the AI mentor fallback. Every check is wrapped
so one failure never breaks the endpoint, and a failing check carries the error
text plus a hint on what to look at. Works in solo and hosted mode (the solo
profile is an admin).
"""

from __future__ import annotations

import json
import time
from urllib.parse import urlparse

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.config import settings
from app.services import instance_config
from app.services.queue import get_redis

HEARTBEAT_KEY = "masdojo:runner:heartbeat"
HEARTBEAT_STALE_SEC = 25


def _c(component: str, status: str, detail: str, hint: str = "") -> dict:
    return {"component": component, "status": status, "detail": detail, "hint": hint}


def _host(url: str) -> str:
    try:
        p = urlparse(url)
        return p.hostname or url
    except Exception:  # noqa: BLE001
        return url


def _check_database(db: Session) -> dict:
    try:
        db.execute(text("SELECT 1"))
        return _c("database", "ok", f"PostgreSQL reachable ({_host(settings.database_url)})")
    except Exception as exc:  # noqa: BLE001
        return _c(
            "database",
            "down",
            f"{type(exc).__name__}: {str(exc)[:160]}",
            "check the db container is up (docker compose ps db) and DATABASE_URL",
        )


def _redis_client_or_error() -> tuple[object | None, dict | None]:
    try:
        client = get_redis()
        client.ping()
        return client, _c("redis", "ok", f"queue backend reachable ({_host(settings.redis_url)})")
    except Exception as exc:  # noqa: BLE001
        return None, _c(
            "redis",
            "down",
            f"{type(exc).__name__}: {str(exc)[:160]}",
            "check the redis container is up (docker compose ps redis) and REDIS_URL",
        )


def _check_runner_and_emulator(client) -> list[dict]:
    # Read heartbeat + queue depth; tolerate any redis hiccup.
    hb = None
    queued = None
    try:
        raw = client.get(HEARTBEAT_KEY)
        hb = json.loads(raw) if raw else None
        queued = client.llen(settings.grading_queue)
    except Exception:  # noqa: BLE001
        pass

    age = None
    if hb:
        try:
            age = time.time() - float(hb.get("ts", 0))
        except (TypeError, ValueError):
            age = None

    checks: list[dict] = []
    qnote = f"; {queued} job(s) queued" if queued else ""

    if hb and age is not None and age < HEARTBEAT_STALE_SEC:
        mode = hb.get("mode", "unknown")
        checks.append(_c("runner", "ok", f"up ({mode}), last seen {int(age)}s ago{qnote}"))
        if mode == "dry-run":
            checks.append(
                _c(
                    "emulator",
                    "disabled",
                    "dry-run runner by design: grades flag/static tasks, no device",
                    "start a KVM runner (make up) and set LAB_SHELL_COMMAND to adb for live grading",
                )
            )
        else:
            checks.append(_c("emulator", "ok", f"device {hb.get('device') or 'unknown'} ({mode})"))
    elif hb and age is not None:
        # Stale heartbeat: the runner was here but stopped refreshing.
        checks.append(
            _c(
                "runner",
                "down",
                f"stale heartbeat, last seen {int(age)}s ago{qnote}",
                "the runner process likely crashed or lost Redis; check its logs "
                "(docker compose logs runner / runner-dryrun)",
            )
        )
        checks.append(_c("emulator", "down", "no live runner, so no device", "bring the runner back up"))
    else:
        checks.append(
            _c(
                "runner",
                "down",
                f"no runner heartbeat{qnote}",
                "no grader is consuming the queue; start one with `make runner-dryrun` "
                "(no KVM) or `make up` (KVM). Submitted jobs stay queued until then.",
            )
        )
        checks.append(_c("emulator", "down", "no runner connected, so no device", "start a runner"))
    return checks


def _check_lab(db: Session) -> dict:
    env_on = settings.lab_enabled
    admin_on = instance_config.lab_enabled(db)
    if env_on and admin_on:
        return _c("lab_playground", "ok", settings.lab_shell_command)
    reason = "disabled by admin (Instance settings)" if env_on else "disabled by env (LAB_ENABLED=false)"
    return _c("lab_playground", "disabled", reason, "enable it in Admin > Instance settings")


def _check_ai(db: Session) -> dict:
    cfg = instance_config.get_config(db)
    if cfg.ai_fallback_key_encrypted:
        return _c(
            "ai_mentor",
            "ok",
            f"fallback: {cfg.ai_fallback_provider}/{cfg.ai_fallback_model or 'default'}",
        )
    return _c(
        "ai_mentor",
        "warn",
        "no install fallback configured",
        "optional: set a fallback in Instance settings, or users bring their own key",
    )


def run_checks(db: Session) -> list[dict]:
    """Return component checks. status is ok | warn | down | disabled. Each entry
    carries a human detail and, when actionable, a hint."""
    checks: list[dict] = [_check_database(db)]

    client, redis_check = _redis_client_or_error()
    checks.append(redis_check)
    if client is not None:
        checks.extend(_check_runner_and_emulator(client))
    else:
        checks.append(_c("runner", "down", "cannot check: Redis unreachable", "fix Redis first"))
        checks.append(_c("emulator", "down", "cannot check: Redis unreachable", "fix Redis first"))

    checks.append(_check_lab(db))
    checks.append(_check_ai(db))
    return checks
