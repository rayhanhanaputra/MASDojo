"""Profile / stats routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_role
from app.db.session import get_db
from app.models.progress import Progress
from app.models.task import Task
from app.models.user import User
from app.schemas.stats import ProfileStats, RosterEntry
from app.services import profile_stats

router = APIRouter(prefix="/stats", tags=["stats"])


@router.get("", response_model=ProfileStats)
def my_stats(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> ProfileStats:
    return profile_stats.compute(db, user)


@router.get("/roster", response_model=list[RosterEntry])
def roster(
    db: Session = Depends(get_db),
    _staff: User = Depends(require_role("instructor")),
) -> list[RosterEntry]:
    """Lightweight learner roster with headline progress, for staff."""
    total_tasks = db.scalar(select(func.count(Task.id))) or 0
    passed = dict(
        db.execute(
            select(Progress.user_id, func.count())
            .where(Progress.passed.is_(True))
            .group_by(Progress.user_id)
        ).all()
    )
    scored = dict(
        db.execute(
            select(Progress.user_id, func.coalesce(func.sum(Progress.best_score), 0))
            .where(Progress.passed.is_(True))
            .group_by(Progress.user_id)
        ).all()
    )
    return [
        RosterEntry(
            id=u.id,
            email=u.email,
            display_name=u.display_name,
            role=u.role,
            tasks_passed=int(passed.get(u.id, 0)),
            tasks_total=total_tasks,
            total_score=int(scored.get(u.id, 0)),
        )
        for u in db.scalars(select(User).order_by(User.id))
    ]


@router.get("/users/{user_id}", response_model=ProfileStats)
def user_stats(
    user_id: int,
    db: Session = Depends(get_db),
    _staff: User = Depends(require_role("instructor")),
) -> ProfileStats:
    """Any user's stats, for instructors and admins."""
    target = db.get(User, user_id)
    if target is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "user not found")
    return profile_stats.compute(db, target)
