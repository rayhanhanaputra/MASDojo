"""Submission routes: submit a solution, poll its grade, list history."""

from __future__ import annotations

import json
import time
from collections.abc import Iterator
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from loguru import logger
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import create_stream_token, decode_access_token
from app.db.session import SessionLocal
from app.services.queue import get_redis

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.progress import Progress
from app.models.submission import (
    STATUS_ERROR,
    STATUS_FAILED,
    STATUS_PASSED,
    STATUS_QUEUED,
    Submission,
)
from app.models.task import Task
from app.models.user import User
from app.schemas.submission import SubmissionPublic, SubmitRequest
from app.services.queue import enqueue_grading_job

router = APIRouter(prefix="/submissions", tags=["submissions"])

# Required payload field per success type.
_REQUIRED_FIELD = {
    "flag": "flag",
    "static_assert": "value",
    "frida_assert": "script",
    "network_assert": None,  # interaction observed live; payload optional
}


def _validate_payload(success_type: str, payload: dict) -> None:
    field = _REQUIRED_FIELD.get(success_type)
    if field is None:
        return
    value = payload.get(field)
    if not isinstance(value, str) or not value.strip():
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            f"submission for '{success_type}' requires a non-empty '{field}' string",
        )


def _now() -> datetime:
    return datetime.now(timezone.utc)


@router.post("/{task_id}", response_model=SubmissionPublic, status_code=status.HTTP_202_ACCEPTED)
def submit(
    task_id: str,
    body: SubmitRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> Submission:
    task = db.get(Task, task_id)
    if not task:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Task not found")
    if task.grader_status != "implemented":
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            "This task's grader is not implemented yet (scaffolded task).",
        )

    _validate_payload(task.success_type, body.payload)

    submission = Submission(
        user_id=user.id,
        task_id=task_id,
        success_type=task.success_type,
        payload=body.payload,
        status=STATUS_QUEUED,
    )
    db.add(submission)

    # Update attempt counters on progress.
    progress = db.scalar(
        select(Progress).where(Progress.user_id == user.id, Progress.task_id == task_id)
    )
    now = _now()
    if progress is None:
        progress = Progress(
            user_id=user.id,
            task_id=task_id,
            domain=task.domain,
            difficulty=task.difficulty,
            attempts=1,
            first_attempt_at=now,
            last_attempt_at=now,
        )
        db.add(progress)
    else:
        progress.attempts += 1
        progress.last_attempt_at = now
        if progress.first_attempt_at is None:
            progress.first_attempt_at = now

    db.flush()  # assign submission.id
    job_id = enqueue_grading_job(submission.id, task_id, task.package_path)
    submission.job_id = job_id
    db.commit()
    db.refresh(submission)
    logger.info("user {} submitted task {} (submission {})", user.id, task_id, submission.id)
    return submission


@router.get("/{submission_id}", response_model=SubmissionPublic)
def get_submission(
    submission_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> Submission:
    submission = db.get(Submission, submission_id)
    if not submission or submission.user_id != user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Submission not found")
    return submission


@router.get("/{submission_id}/stream-token")
def stream_token(
    submission_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict[str, str]:
    """Mint a short-lived, stream-scoped token for the SSE endpoint."""
    submission = db.get(Submission, submission_id)
    if not submission or submission.user_id != user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Submission not found")
    return {"token": create_stream_token(user.id, submission_id)}


_TERMINAL = {STATUS_PASSED, STATUS_FAILED, STATUS_ERROR}


@router.get("/{submission_id}/stream")
def stream_grading_events(
    submission_id: int,
    token: str = Query(..., description="stream-scoped token from /stream-token"),
) -> StreamingResponse:
    """Server-Sent Events stream of live grading steps for a submission.

    Auth and ownership are resolved up front in a short-lived session that closes
    before streaming begins — the generator never holds a pooled DB connection.
    Replays already-emitted steps, then follows Redis pub/sub until the verdict;
    if the submission already finished it emits a synthetic done and closes.
    """
    payload = decode_access_token(token)
    if not payload or payload.get("scope") != "stream" or payload.get("sid") != submission_id:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid stream token")
    try:
        user_id = int(payload["sub"])
    except (KeyError, TypeError, ValueError):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid stream token")

    # Resolve ownership + active user in a session that closes immediately.
    with SessionLocal() as db:
        user = db.get(User, user_id)
        submission = db.get(Submission, submission_id)
        if user is None or not user.is_active:
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid stream token")
        if not submission or submission.user_id != user_id:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Submission not found")
        already_terminal = submission.status in _TERMINAL

    channel = f"masdojo:events:{submission_id}"
    replay_key = f"masdojo:eventlog:{submission_id}"

    def _is_done(raw: str) -> bool:
        try:
            return json.loads(raw).get("level") == "done"
        except (ValueError, TypeError):
            return False

    def event_gen() -> Iterator[str]:
        client = get_redis()
        saw_done = False
        for raw in client.lrange(replay_key, 0, -1):
            yield f"data: {raw}\n\n"
            if _is_done(raw):
                saw_done = True
                return
        # If the job already finished and the done marker wasn't in the replay
        # (lost/expired), synthesize one so the client closes instead of idling.
        if already_terminal and not saw_done:
            yield 'data: {"level":"done","phase":"done","msg":"grading complete"}\n\n'
            return

        pubsub = client.pubsub()
        pubsub.subscribe(channel)
        deadline = time.time() + settings.grading_job_timeout_sec + 30
        try:
            while time.time() < deadline:
                msg = pubsub.get_message(timeout=1.0, ignore_subscribe_messages=True)
                if msg is None:
                    yield ": keep-alive\n\n"  # heartbeat
                    continue
                raw = msg["data"]
                yield f"data: {raw}\n\n"
                if _is_done(raw):
                    return
        finally:
            try:
                pubsub.close()
            except Exception:  # noqa: BLE001
                pass

    return StreamingResponse(
        event_gen(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.get("", response_model=list[SubmissionPublic])
def list_submissions(
    task_id: str | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> list[Submission]:
    stmt = select(Submission).where(Submission.user_id == user.id)
    if task_id:
        stmt = stmt.where(Submission.task_id == task_id)
    stmt = stmt.order_by(Submission.created_at.desc())
    return list(db.scalars(stmt).all())
