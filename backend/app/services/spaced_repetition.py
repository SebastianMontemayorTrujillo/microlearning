import math
from datetime import datetime, timedelta

from app.models import Mastery


def retention(state: Mastery, now: datetime) -> float:
    if state.last_reviewed is None:
        return 1.0
    elapsed = max(0.0, (now - state.last_reviewed).total_seconds() / 86400)
    # A scheduled interval corresponds to approximately 80% predicted retention.
    return math.exp(math.log(0.8) * elapsed / max(0.25, state.interval_days))


def urgency(state: Mastery, now: datetime) -> float:
    if state.next_review is None:
        return 0.0
    days_overdue = (now - state.next_review).total_seconds() / 86400
    if days_overdue < 0:
        return 0.25 * (1 - retention(state, now))
    return min(1.0, 0.7 + 0.3 * days_overdue / max(1.0, state.interval_days))


def schedule(state: Mastery, correct: bool, now: datetime, confident: bool = True) -> None:
    spaced = state.last_retrieval is None or (now - state.last_retrieval).total_seconds() >= 20 * 3600
    if correct:
        if spaced:
            state.retrieval_streak += 1
            ladder = [1.0, 3.0, 7.0, 14.0, 30.0]
            step = ladder[min(state.retrieval_streak - 1, len(ladder) - 1)]
            state.interval_days = min(90.0, max(step, state.interval_days * (2.0 if confident else 1.35)))
            state.next_review = now + timedelta(days=state.interval_days)
            state.last_reviewed = now
        elif state.next_review is None or state.next_review <= now:
            state.interval_days = max(1.0, state.interval_days)
            state.next_review = now + timedelta(days=state.interval_days)
            state.last_reviewed = now
        # Immediate repeat successes cannot keep moving a future due date.
    else:
        state.retrieval_streak = 0
        state.interval_days = max(0.25, state.interval_days * 0.35)
        state.next_review = now + timedelta(minutes=10)
        state.last_reviewed = now
    state.last_retrieval = now
