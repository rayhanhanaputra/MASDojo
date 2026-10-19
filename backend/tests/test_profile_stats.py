"""Profile stats: rollups must come out in curriculum order, never alphabetical.

Modules are numeric strings ("1".."11") and order_index restarts per module, so
a naive string/alpha sort would mis-order both modules (10 between 1 and 2) and
domains (A-Z instead of teaching order). These tests pin the correct ordering.
"""

from __future__ import annotations

from app.db.session import SessionLocal
from app.models.task import Task
from app.models.user import User
from app.services import profile_stats


def _task(task_id: str, module: str, order_index: int, domain: str) -> Task:
    return Task(
        id=task_id,
        title=task_id,
        module=module,
        order_index=order_index,
        domain=domain,
        masvs=[],
        mastg_refs=[],
        difficulty=1,
        prereqs=[],
        objective="o",
        success_type="static_assert",
        submission_schema={"value": "string"},
        hints={},
        is_reference=False,
        grader_status="implemented",
        package_path=f"tasks/{task_id}",
    )


def _make_user(db) -> User:
    u = User(
        email="order@example.com",
        display_name="Order",
        hashed_password="x",
        role="learner",
        is_active=True,
    )
    db.add(u)
    db.commit()
    db.refresh(u)
    return u


def test_domains_and_modules_follow_numeric_curriculum_order(client):
    # Seeded deliberately out of order. Domain names are chosen so that their
    # alphabetical order ([alpha, mike, zulu]) differs from curriculum order.
    with SessionLocal() as db:
        db.add_all(
            [
                _task("t10", module="10", order_index=1, domain="mike"),
                _task("t2", module="2", order_index=1, domain="alpha"),
                _task("t1b", module="1", order_index=2, domain="zulu"),
                _task("t1a", module="1", order_index=1, domain="zulu"),
            ]
        )
        db.commit()
        user = _make_user(db)
        stats = profile_stats.compute(db, user)

    # Modules numeric, not string ("10" must come LAST, not between 1 and 2).
    assert [m.module for m in stats.modules] == ["1", "2", "10"]
    # Domains in order of first curriculum appearance, not A-Z.
    assert [d.domain for d in stats.domains] == ["zulu", "alpha", "mike"]
    # Per-task list: numeric module then order_index (t1a before t1b).
    assert [t.task_id for t in stats.tasks] == ["t1a", "t1b", "t2", "t10"]


def test_non_numeric_module_label_does_not_crash_sort(client):
    with SessionLocal() as db:
        db.add_all(
            [
                _task("tz", module="2", order_index=1, domain="d2"),
                _task("tx", module="intro", order_index=1, domain="d0"),
            ]
        )
        db.commit()
        user = _make_user(db)
        stats = profile_stats.compute(db, user)

    # Numeric modules sort ahead of any non-numeric label; no exception raised.
    assert [m.module for m in stats.modules] == ["2", "intro"]
