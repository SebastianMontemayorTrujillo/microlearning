from datetime import datetime, timedelta

from app.models import Mastery
from app.services.spaced_repetition import retention, schedule


def clamp(value: float) -> float:
    return max(0.0, min(1.0, value))


def effective_mastery(state: Mastery, now: datetime) -> float:
    return state.mastery * retention(state, now)


def is_mastered(state: Mastery, now: datetime) -> bool:
    return state.times_seen > 0 and effective_mastery(state, now) >= 0.8 and state.retrieval_streak >= 3


def update_mastery(
    state: Mastery,
    kind: str,
    difficulty: float,
    now: datetime,
    correct: bool | None = None,
    seconds: float = 0,
) -> None:
    if kind == "shown":
        state.times_seen += 1
        state.last_seen = now
    elif kind == "answer" and correct is not None:
        recent = state.last_retrieval is not None and (now - state.last_retrieval).total_seconds() < 20 * 3600
        evidence = 0.25 if recent else 1.0
        prior = effective_mastery(state, now)
        if correct:
            state.correct_answers += 1
            gain = (0.27 + difficulty * 0.15) * evidence
            state.mastery = clamp(prior + gain * (1.0 - prior))
        else:
            state.incorrect_answers += 1
            loss = (0.3 + (1.0 - difficulty) * 0.12) * max(0.5, evidence)
            state.mastery = clamp(prior * (1.0 - loss))
        state.confidence = clamp(state.confidence + 0.12 * evidence * (1 - state.confidence))
        schedule(state, correct, now, confident=state.mastery >= 0.5)
        # The updated probability is a belief at `now`; anchor decay here to avoid
        # applying the same elapsed forgetting twice after an early retrieval.
        state.last_reviewed = now
    elif kind == "known":
        # Self-report is weaker than retrieval and cannot certify mastery.
        state.mastery = max(state.mastery, min(0.45, state.mastery + 0.08))
        if state.next_review is None:
            state.next_review = now + timedelta(days=1)
            state.interval_days = 1.0
            state.last_reviewed = now
    elif kind == "dwell" and seconds >= 12:
        state.mastery = max(state.mastery, min(0.25, state.mastery + min(0.025, seconds / 2400)))
        state.interest = clamp(state.interest + 0.01)
        if state.next_review is None:
            state.next_review = now + timedelta(days=1)
            state.interval_days = 1.0
            state.last_reviewed = now
    elif kind in ("deeper", "tutor", "saved"):
        state.interest = clamp(state.interest + 0.04 * (1 - state.interest))
    elif kind == "skipped":
        state.interest = clamp(state.interest - 0.015)
    # Revisiting is logged, but it is not proof of learning.
