"""Profile / stats routes."""

from __future__ import annotations

from collections import defaultdict

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.hint_usage import HintUsage
from app.models.progress import Progress
from app.models.task import Task
from app.models.user import User
from app.schemas.stats import DomainMastery, ProfileStats

router = APIRouter(prefix="/stats", tags=["stats"])


@router.get("", response_model=ProfileStats)
def profile_stats(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> ProfileStats:
    tasks = list(db.scalars(select(Task)).all())
    tasks_by_domain: dict[str, list[Task]] = defaultdict(list)
    for t in tasks:
        tasks_by_domain[t.domain].append(t)

    progress_rows = list(
        db.scalars(select(Progress).where(Progress.user_id == user.id)).all()
    )
    progress_by_id = {p.task_id: p for p in progress_rows}

    total_hints = db.scalar(
        select(func.count(HintUsage.id)).where(HintUsage.user_id == user.id)
    ) or 0

    domains: list[DomainMastery] = []
    tasks_passed = total_score = total_attempts = 0

    for domain, domain_tasks in sorted(tasks_by_domain.items()):
        passed = 0
        scores: list[int] = []
        highest_diff = 0
        for t in domain_tasks:
            p = progress_by_id.get(t.id)
            if not p:
                continue
            total_attempts += p.attempts
            if p.passed:
                passed += 1
                tasks_passed += 1
                total_score += p.best_score
                scores.append(p.best_score)
                highest_diff = max(highest_diff, t.difficulty)
        domains.append(
            DomainMastery(
                domain=domain,
                tasks_total=len(domain_tasks),
                tasks_passed=passed,
                avg_score=round(sum(scores) / len(scores), 1) if scores else 0.0,
                highest_difficulty_cleared=highest_diff,
            )
        )

    return ProfileStats(
        display_name=user.display_name,
        tasks_passed=tasks_passed,
        tasks_total=len(tasks),
        total_score=total_score,
        total_attempts=total_attempts,
        total_hints_used=total_hints,
        domains=domains,
    )
