"""Compute a user's profile stats. Shared by the learner's own /stats route and
by the admin/instructor view of any user's progress.

Produces a comprehensive picture: headline summary (completion, pass rate, avg
attempts per pass, difficulty cleared, MASVS coverage, activity window), per
domain and per module rollups, and a per-task breakdown.
"""

from __future__ import annotations

from collections import defaultdict

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.hint_usage import HintUsage
from app.models.progress import Progress
from app.models.task import Task
from app.models.user import User
from app.schemas.stats import DomainMastery, ModuleProgress, ProfileStats, TaskStat


def _min_dt(a, b):
    if a is None:
        return b
    if b is None:
        return a
    return a if a < b else b


def _max_dt(a, b):
    if a is None:
        return b
    if b is None:
        return a
    return a if a > b else b


def compute(db: Session, user: User) -> ProfileStats:
    tasks = list(db.scalars(select(Task)).all())
    progress_by_id = {
        p.task_id: p for p in db.scalars(select(Progress).where(Progress.user_id == user.id)).all()
    }
    total_hints = (
        db.scalar(select(func.count(HintUsage.id)).where(HintUsage.user_id == user.id)) or 0
    )

    by_domain: dict[str, list[Task]] = defaultdict(list)
    by_module: dict[str, list[Task]] = defaultdict(list)
    for t in tasks:
        by_domain[t.domain].append(t)
        by_module[t.module].append(t)

    task_stats: list[TaskStat] = []
    masvs: set[str] = set()
    tasks_passed = tasks_attempted = total_score = total_attempts = 0
    highest_diff = 0
    solve_times: list[int] = []
    first_active = last_active = None

    for t in tasks:
        p = progress_by_id.get(t.id)
        attempts = p.attempts if p else 0
        passed = bool(p and p.passed)
        best = p.best_score if p else 0
        if p:
            total_attempts += attempts
            first_active = _min_dt(first_active, p.first_attempt_at)
            last_active = _max_dt(last_active, p.last_attempt_at)
        if attempts > 0 or passed:
            tasks_attempted += 1
        if passed:
            tasks_passed += 1
            total_score += best
            highest_diff = max(highest_diff, t.difficulty)
            for c in t.masvs or []:
                masvs.add(c)
            if p and p.time_to_solve_sec:
                solve_times.append(p.time_to_solve_sec)
        status = "passed" if passed else ("attempted" if attempts > 0 else "not_started")
        task_stats.append(
            TaskStat(
                task_id=t.id,
                title=t.title,
                module=t.module,
                domain=t.domain,
                difficulty=t.difficulty,
                success_type=t.success_type,
                status=status,
                best_score=best,
                attempts=attempts,
                hint_tier_used=p.max_hint_tier if p else 0,
                time_to_solve_sec=p.time_to_solve_sec if p else None,
                last_activity=p.last_attempt_at if p else None,
                passed_at=p.passed_at if p else None,
            )
        )

    domains: list[DomainMastery] = []
    for domain, dts in sorted(by_domain.items()):
        scores = [
            progress_by_id[t.id].best_score
            for t in dts
            if t.id in progress_by_id and progress_by_id[t.id].passed
        ]
        passed = sum(1 for t in dts if t.id in progress_by_id and progress_by_id[t.id].passed)
        hd = max(
            (t.difficulty for t in dts if t.id in progress_by_id and progress_by_id[t.id].passed),
            default=0,
        )
        domains.append(
            DomainMastery(
                domain=domain,
                tasks_total=len(dts),
                tasks_passed=passed,
                avg_score=round(sum(scores) / len(scores), 1) if scores else 0.0,
                highest_difficulty_cleared=hd,
            )
        )

    modules = [
        ModuleProgress(
            module=module,
            tasks_total=len(mts),
            tasks_passed=sum(
                1 for t in mts if t.id in progress_by_id and progress_by_id[t.id].passed
            ),
        )
        for module, mts in sorted(by_module.items(), key=lambda kv: kv[0])
    ]

    total_tasks = len(tasks)
    # Keep the per-task list in curriculum order (module, then order_index).
    task_stats.sort(key=lambda s: (s.module, s.task_id))

    return ProfileStats(
        display_name=user.display_name,
        tasks_passed=tasks_passed,
        tasks_total=total_tasks,
        total_score=total_score,
        total_attempts=total_attempts,
        total_hints_used=total_hints,
        tasks_attempted=tasks_attempted,
        completion_pct=round(100 * tasks_passed / total_tasks, 1) if total_tasks else 0.0,
        pass_rate=round(100 * tasks_passed / tasks_attempted, 1) if tasks_attempted else 0.0,
        avg_attempts_per_pass=round(total_attempts / tasks_passed, 1) if tasks_passed else 0.0,
        highest_difficulty_cleared=highest_diff,
        avg_time_to_solve_min=(
            round(sum(solve_times) / len(solve_times) / 60, 1) if solve_times else 0.0
        ),
        masvs_covered=sorted(masvs),
        first_active=first_active,
        last_active=last_active,
        domains=domains,
        modules=modules,
        tasks=task_stats,
    )
