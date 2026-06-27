"""Tests for the adaptive pathway engine."""

from __future__ import annotations

from datetime import datetime, timezone

from app.db.session import SessionLocal
from app.models.progress import Progress
from app.models.task import Task
from app.services.pathway import (
    STATE_AVAILABLE,
    STATE_LOCKED,
    STATE_PASSED,
    PathwayEngine,
)


def _task(db, id_, *, module, order, domain, difficulty, prereqs, ref=False):
    db.add(
        Task(
            id=id_,
            title=id_,
            module=module,
            order_index=order,
            domain=domain,
            masvs=[],
            mastg_refs=[],
            difficulty=difficulty,
            prereqs=prereqs,
            objective="",
            success_type="flag",
            submission_schema={},
            hints={},
            is_reference=ref,
            grader_status="implemented",
            package_path=f"tasks/{id_}",
        )
    )


def _seed_user(client):
    client.post(
        "/auth/register",
        json={"email": "p@e.com", "display_name": "P", "password": "password123"},
    )
    from app.models.user import User

    with SessionLocal() as db:
        return db.query(User).filter_by(email="p@e.com").one().id


def test_states_lock_until_prereqs_pass(client):
    user_id = _seed_user(client)
    with SessionLocal() as db:
        _task(db, "a", module="0", order=1, domain="foundations", difficulty=1, prereqs=[])
        _task(db, "b", module="1", order=1, domain="static-re", difficulty=1, prereqs=["a"])
        _task(db, "c", module="1", order=2, domain="static-re", difficulty=2, prereqs=["b"])
        db.commit()

        nodes, recommended = PathwayEngine().skill_map(db, user_id)
        state = {t.id: s for t, s in nodes}
        assert state["a"] == STATE_AVAILABLE
        assert state["b"] == STATE_LOCKED
        assert state["c"] == STATE_LOCKED
        # With nothing passed, the only available task is the entry point.
        assert recommended.id == "a"


def test_recommend_favours_weakest_domain_and_difficulty(client):
    user_id = _seed_user(client)
    now = datetime.now(timezone.utc)
    with SessionLocal() as db:
        # Two independent entry points in different domains.
        _task(db, "foundations-1", module="0", order=1, domain="foundations", difficulty=1, prereqs=[])
        _task(db, "static-1", module="1", order=1, domain="static-re", difficulty=1, prereqs=[])
        _task(db, "static-2", module="1", order=2, domain="static-re", difficulty=2, prereqs=["static-1"])
        # Learner already cleared the foundations domain entirely.
        db.add(
            Progress(
                user_id=user_id,
                task_id="foundations-1",
                domain="foundations",
                difficulty=1,
                attempts=1,
                passed=True,
                best_score=100,
                passed_at=now,
            )
        )
        db.commit()

        nodes, recommended = PathwayEngine().skill_map(db, user_id)
        state = {t.id: s for t, s in nodes}
        assert state["foundations-1"] == STATE_PASSED
        assert state["static-1"] == STATE_AVAILABLE
        assert state["static-2"] == STATE_LOCKED
        # static-re is the weaker (0% cleared) domain, so static-1 is recommended.
        assert recommended.id == "static-1"
