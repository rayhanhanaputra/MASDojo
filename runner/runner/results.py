"""Persist grading results back to Postgres.

The runner is decoupled from the backend's ORM: it issues parameterised UPDATEs
against the `submissions` and `progress` tables via SQLAlchemy Core. This keeps
the two services independent while sharing one database.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone

from loguru import logger
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

from runner.config import config
from runner.grader_api import GradeResult

# Score penalties mirror the backend's scoring module so a passing grade earns a
# consistent score regardless of which service computes it.
_BASE_PER_DIFFICULTY = 100
_HINT_PENALTY = {0: 0, 1: 10, 2: 20, 3: 35, 4: 70}
_ATTEMPT_PENALTY = 8
_MIN_PASS_SCORE = 10


def _engine() -> Engine:
    return create_engine(config.database_url, pool_pre_ping=True, future=True)


def _score(difficulty: int, max_hint_tier: int, attempts: int) -> int:
    base = _BASE_PER_DIFFICULTY * max(1, difficulty)
    hint_loss = _HINT_PENALTY.get(max_hint_tier, 70)
    attempt_loss = _ATTEMPT_PENALTY * max(0, attempts - 1)
    return max(_MIN_PASS_SCORE, base - hint_loss - attempt_loss)


class ResultWriter:
    def __init__(self) -> None:
        self._engine = _engine()

    def mark_running(self, submission_id: int) -> None:
        with self._engine.begin() as conn:
            conn.execute(
                text("UPDATE submissions SET status='running' WHERE id=:id"),
                {"id": submission_id},
            )

    def record_result(self, submission_id: int, task_id: str, result: GradeResult) -> None:
        now = datetime.now(timezone.utc)
        status = "passed" if result.passed else "failed"
        with self._engine.begin() as conn:
            row = conn.execute(
                text("SELECT user_id, ai_generated FROM submissions WHERE id=:id"),
                {"id": submission_id},
            ).first()
            if row is None:
                logger.error("submission {} vanished before result write", submission_id)
                return
            user_id, ai_generated = row[0], bool(row[1])

            # AI-as-adversary attempts are graded identically but must never
            # affect the learner's own progress or score.
            if ai_generated:
                score = 0
            else:
                score = self._update_progress(conn, user_id, task_id, result.passed, now)

            conn.execute(
                text(
                    """
                    UPDATE submissions
                    SET status=:status,
                        evidence=:evidence,
                        checks=:checks,
                        evidence_bundle=:evidence_bundle,
                        score=:score,
                        error=NULL,
                        completed_at=:completed_at
                    WHERE id=:id
                    """
                ),
                {
                    "status": status,
                    "evidence": result.evidence,
                    "checks": json.dumps([c.to_dict() for c in result.checks]),
                    "evidence_bundle": json.dumps(
                        [e.to_dict() for e in result.evidence_items]
                    ),
                    "score": score if result.passed else 0,
                    "completed_at": now,
                    "id": submission_id,
                },
            )
        logger.info("submission {} -> {} (score {})", submission_id, status, score)

    def _update_progress(self, conn, user_id: int, task_id: str, passed: bool, now) -> int:
        prog = conn.execute(
            text(
                "SELECT id, attempts, max_hint_tier, difficulty, passed, best_score, "
                "first_attempt_at FROM progress WHERE user_id=:u AND task_id=:t"
            ),
            {"u": user_id, "t": task_id},
        ).mappings().first()

        if prog is None:
            # Defensive: the backend creates progress on submit, but tolerate races.
            difficulty = conn.execute(
                text("SELECT difficulty FROM tasks WHERE id=:t"), {"t": task_id}
            ).scalar() or 1
            attempts, max_hint_tier, already_passed, best_score = 1, 0, False, 0
            first_attempt_at = now
        else:
            difficulty = prog["difficulty"] or 1
            attempts = prog["attempts"] or 1
            max_hint_tier = prog["max_hint_tier"] or 0
            already_passed = prog["passed"]
            best_score = prog["best_score"] or 0
            first_attempt_at = prog["first_attempt_at"] or now

        score = _score(difficulty, max_hint_tier, attempts) if passed else 0

        if prog is None:
            return score

        if passed:
            tts = int((now - first_attempt_at).total_seconds()) if first_attempt_at else None
            conn.execute(
                text(
                    """
                    UPDATE progress
                    SET passed=true,
                        best_score=GREATEST(best_score, :score),
                        passed_at=COALESCE(passed_at, :now),
                        time_to_solve_sec=COALESCE(time_to_solve_sec, :tts)
                    WHERE id=:id
                    """
                ),
                {"score": score, "now": now, "tts": tts, "id": prog["id"]},
            )
        return max(score, best_score)

    def record_error(self, submission_id: int, message: str) -> None:
        with self._engine.begin() as conn:
            conn.execute(
                text(
                    "UPDATE submissions SET status='error', error=:err, "
                    "completed_at=:now WHERE id=:id"
                ),
                {
                    "err": message[:4000],
                    "now": datetime.now(timezone.utc),
                    "id": submission_id,
                },
            )
        logger.error("submission {} errored: {}", submission_id, message)
