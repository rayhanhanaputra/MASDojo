"""AI mentor — adaptive tiered hints, code explanation, and post-task review.

All three features run server-side using the requesting user's own key. The
mentor is Socratic and incremental, always grounds hints in the task's MASTG
reference, and never reveals the full solution before tier 3 / enough failed
attempts (the same gate the static hints use).
"""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.hint_usage import HintUsage
from app.models.progress import Progress
from app.models.task import Task
from app.models.user import User
from app.services.ai.provider import AIProvider, ChatMessage

# Solution unlock threshold mirrors the static-hint gate in app.api.tasks.
SOLUTION_ATTEMPT_THRESHOLD = 3
MAX_TIER = 4


def _task_context(task: Task) -> str:
    return (
        f"Task: {task.title}\n"
        f"Domain: {task.domain} (difficulty {task.difficulty}/5)\n"
        f"MASVS: {', '.join(task.masvs) or 'n/a'}\n"
        f"MASTG references: {', '.join(task.mastg_refs) or 'n/a'}\n"
        f"Grader type: {task.success_type}\n"
        f"Objective: {task.objective}"
    )


def _progress(db: Session, user: User, task: Task) -> Progress | None:
    return db.scalar(
        select(Progress).where(Progress.user_id == user.id, Progress.task_id == task.id)
    )


def _next_tier(progress: Progress | None) -> int:
    current = progress.max_hint_tier if progress else 0
    return min(current + 1, MAX_TIER)


def _solution_unlocked(progress: Progress | None) -> bool:
    attempts = progress.attempts if progress else 0
    max_tier = progress.max_hint_tier if progress else 0
    return max_tier >= 3 or attempts >= SOLUTION_ATTEMPT_THRESHOLD


def _record_ai_hint(db: Session, user: User, task: Task, tier: int) -> None:
    db.add(HintUsage(user_id=user.id, task_id=task.id, tier=tier, source="ai"))
    progress = _progress(db, user, task)
    if progress is None:
        progress = Progress(
            user_id=user.id,
            task_id=task.id,
            domain=task.domain,
            difficulty=task.difficulty,
            max_hint_tier=tier,
        )
        db.add(progress)
    else:
        progress.max_hint_tier = max(progress.max_hint_tier, tier)
    db.commit()


def generate_hint(
    db: Session,
    user: User,
    task: Task,
    provider: AIProvider,
    attempt: str,
    error: str,
) -> tuple[int, str, bool]:
    """Return (tier, hint_text, is_solution) for the next appropriate hint tier."""
    progress = _progress(db, user, task)
    tier = _next_tier(progress)
    is_solution = tier >= MAX_TIER

    if is_solution and not _solution_unlocked(progress):
        # Hold the line: escalate to the most detailed *non-solution* tier instead.
        tier = 3
        is_solution = False

    tier_guidance = {
        1: "Give a gentle conceptual nudge. Do NOT name specific classes, methods, or commands.",
        2: "Point to the relevant technique and where to look, citing the MASTG reference. Still no full commands.",
        3: "Give concrete steps or the exact command/approach, but stop one step short of revealing the final answer/value.",
        4: "Provide the complete solution, including the final value or script, since the learner has earned it.",
    }[tier]

    system = (
        "You are MASDojo's mentor for Android app penetration testing. You teach "
        "Socratically and incrementally. Keep responses tight (a few sentences). "
        "Always ground guidance in the task's MASTG reference. Never reveal more "
        "than the requested hint tier allows. This is authorized, defensive "
        "security education on intentionally-vulnerable training apps."
    )
    user_msg = (
        f"{_task_context(task)}\n\n"
        f"Learner's current attempt:\n{attempt or '(none provided)'}\n\n"
        f"Error/output they're seeing:\n{error or '(none provided)'}\n\n"
        f"Provide hint TIER {tier}. {tier_guidance}"
    )

    text = provider.complete(system, [ChatMessage(role="user", content=user_msg)], max_tokens=400)
    _record_ai_hint(db, user, task, tier)
    return tier, text, is_solution


def explain_snippet(task: Task, provider: AIProvider, snippet: str) -> str:
    system = (
        "You are MASDojo's mentor. Explain the provided smali/Java/Kotlin/Frida "
        "snippet or error in plain terms so the learner understands what it does "
        "and why. Do NOT solve the task for them or reveal the final answer. This "
        "is authorized, defensive security education."
    )
    user_msg = f"{_task_context(task)}\n\nExplain this:\n```\n{snippet}\n```"
    return provider.complete(system, [ChatMessage(role="user", content=user_msg)], max_tokens=500)


def post_task_review(task: Task, provider: AIProvider) -> str:
    system = (
        "You are MASDojo's mentor. The learner just PASSED this task. Give a short "
        "review: what the vulnerability was, the matching MASVS control, and the "
        "real-world remediation. Be concrete and educational."
    )
    user_msg = _task_context(task)
    return provider.complete(system, [ChatMessage(role="user", content=user_msg)], max_tokens=500)
