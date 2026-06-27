"""Adaptive pathway engine.

Tasks form a prerequisite DAG grouped by domain. The engine computes each task's
state for a learner (locked / available / passed) and recommends the next task.

The recommendation logic lives behind a `PathwayStrategy` interface so a learned
(ML) strategy can be dropped in later without touching the API. The default is
rule-based: respect prerequisites, ramp difficulty smoothly, favour weaker
domains, and never recommend a task already passed.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections import defaultdict
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.progress import Progress
from app.models.task import Task

STATE_LOCKED = "locked"
STATE_AVAILABLE = "available"
STATE_PASSED = "passed"


@dataclass
class LearnerState:
    """A snapshot of one learner's progress used by the pathway engine."""

    passed_task_ids: set[str]
    attempts_by_task: dict[str, int]
    # domain -> (passed, total)
    domain_counts: dict[str, tuple[int, int]]

    def domain_mastery(self, domain: str) -> float:
        passed, total = self.domain_counts.get(domain, (0, 0))
        return passed / total if total else 0.0


def load_learner_state(db: Session, user_id: int, tasks: list[Task]) -> LearnerState:
    progress = list(db.scalars(select(Progress).where(Progress.user_id == user_id)).all())
    passed_ids = {p.task_id for p in progress if p.passed}
    attempts = {p.task_id: p.attempts for p in progress}

    totals: dict[str, int] = defaultdict(int)
    passed_per_domain: dict[str, int] = defaultdict(int)
    for t in tasks:
        totals[t.domain] += 1
        if t.id in passed_ids:
            passed_per_domain[t.domain] += 1
    domain_counts = {d: (passed_per_domain[d], totals[d]) for d in totals}

    return LearnerState(
        passed_task_ids=passed_ids,
        attempts_by_task=attempts,
        domain_counts=domain_counts,
    )


def task_state(task: Task, state: LearnerState) -> str:
    if task.id in state.passed_task_ids:
        return STATE_PASSED
    if all(pr in state.passed_task_ids for pr in task.prereqs):
        return STATE_AVAILABLE
    return STATE_LOCKED


class PathwayStrategy(ABC):
    """Strategy interface for recommending the next task."""

    @abstractmethod
    def next_task(self, available: list[Task], state: LearnerState) -> Task | None:
        """Pick the best next task from those currently available (unlocked,
        not yet passed), or None if there is nothing to recommend."""


class RuleBasedStrategy(PathwayStrategy):
    """Deterministic recommendation:

    1. Only consider available, not-yet-passed tasks (prereqs already enforced).
    2. Favour the weakest domain (lowest mastery ratio) so learning stays broad.
    3. Within that, ramp difficulty smoothly — prefer the lowest difficulty the
       learner hasn't cleared yet.
    4. Break ties by module/order so the canonical pathway is followed.
    """

    def next_task(self, available: list[Task], state: LearnerState) -> Task | None:
        if not available:
            return None

        def sort_key(task: Task) -> tuple:
            mastery = state.domain_mastery(task.domain)
            # Reference tasks are nudged slightly earlier within a tie so learners
            # hit a fully-working example of each grader type sooner.
            ref_bias = 0 if task.is_reference else 1
            return (
                round(mastery, 3),       # weakest domain first
                task.difficulty,         # smooth difficulty ramp
                int(task.module) if task.module.isdigit() else 99,
                task.order_index,
                ref_bias,
                task.id,
            )

        return sorted(available, key=sort_key)[0]


class PathwayEngine:
    def __init__(self, strategy: PathwayStrategy | None = None) -> None:
        self._strategy = strategy or RuleBasedStrategy()

    def skill_map(self, db: Session, user_id: int) -> tuple[list[tuple[Task, str]], Task | None]:
        tasks = list(
            db.scalars(select(Task).order_by(Task.module, Task.order_index, Task.id)).all()
        )
        state = load_learner_state(db, user_id, tasks)

        nodes: list[tuple[Task, str]] = []
        available: list[Task] = []
        for t in tasks:
            st = task_state(t, state)
            nodes.append((t, st))
            if st == STATE_AVAILABLE:
                available.append(t)

        recommended = self._strategy.next_task(available, state)
        return nodes, recommended
