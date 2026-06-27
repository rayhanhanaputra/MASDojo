"""Score computation: fewer hints and fewer attempts yield a higher score.

A passing submission starts from a difficulty-weighted base and is penalised for
each hint tier revealed and each failed attempt. The result is clamped to a
sane range so a brute-forced solve with every hint still earns a little.
"""

from __future__ import annotations

BASE_PER_DIFFICULTY = 100
HINT_PENALTY = {1: 10, 2: 20, 3: 35, 4: 70}  # tier -> points lost (cumulative max)
ATTEMPT_PENALTY = 8
MIN_PASS_SCORE = 10


def compute_score(difficulty: int, max_hint_tier: int, attempts: int) -> int:
    """Return the score awarded for a passing submission.

    `max_hint_tier` is the highest tier revealed (0..4); `attempts` is the total
    number of attempts including the passing one.
    """
    base = BASE_PER_DIFFICULTY * max(1, difficulty)
    hint_loss = HINT_PENALTY.get(max_hint_tier, 0)
    attempt_loss = ATTEMPT_PENALTY * max(0, attempts - 1)
    return max(MIN_PASS_SCORE, base - hint_loss - attempt_loss)
