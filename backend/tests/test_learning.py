import random
from datetime import datetime, timedelta

import pytest
from sqlalchemy import select

from app.models import LearningCard, Mastery
from app.services.mastery import effective_mastery, update_mastery
from app.services.recommender import prerequisite_readiness, score_candidate, select_feed
from app.services.settings import DEFAULT_WEIGHTS
from app.services.spaced_repetition import retention, schedule, urgency

NOW = datetime(2026, 9, 15, 12)


def test_correct_retrieval_is_stronger_than_reading(db):
    read = db.get(Mastery, "complexity")
    recall = db.get(Mastery, "vectors")
    update_mastery(read, "dwell", 0.3, NOW, seconds=45)
    update_mastery(recall, "answer", 0.3, NOW, correct=True)
    assert recall.mastery > read.mastery * 5
    assert recall.confidence > read.confidence
    assert recall.next_review == NOW + timedelta(days=1)


def test_failures_reduce_mastery_and_bring_review_forward(db):
    state = db.get(Mastery, "complexity")
    state.mastery = 0.8
    state.interval_days = 14
    state.retrieval_streak = 4
    update_mastery(state, "answer", 0.2, NOW, correct=False)
    assert 0 < state.mastery < 0.8
    assert state.interval_days < 14
    assert state.next_review == NOW + timedelta(minutes=10)
    assert state.retrieval_streak == 0


def test_spaced_success_ladder_and_early_repetition(db):
    state = db.get(Mastery, "complexity")
    time = NOW
    for expected in [1, 3, 7, 14, 30]:
        schedule(state, True, time)
        assert state.interval_days == expected
        due = state.next_review
        streak = state.retrieval_streak
        schedule(state, True, time + timedelta(minutes=2))
        assert state.next_review == due
        assert state.retrieval_streak == streak
        time = due


def test_massive_early_repeats_do_not_certify_mastery(db):
    state = db.get(Mastery, "complexity")
    for _ in range(30):
        update_mastery(state, "answer", 0.3, NOW, correct=True)
    assert state.retrieval_streak == 1
    assert state.interval_days == 1
    assert state.next_review == NOW + timedelta(days=1)


def test_self_report_reading_and_interest_are_not_retrieval(db):
    state = db.get(Mastery, "complexity")
    for _ in range(100):
        update_mastery(state, "known", 0.3, NOW)
        update_mastery(state, "dwell", 0.3, NOW, seconds=45)
        update_mastery(state, "deeper", 0.3, NOW)
    assert state.mastery <= 0.45
    assert state.correct_answers == 0
    assert state.confidence == 0
    assert 0.5 < state.interest <= 1
    assert state.retrieval_streak == 0


def test_predicted_retention_and_urgency(db):
    state = db.get(Mastery, "complexity")
    state.mastery = 0.8
    schedule(state, True, NOW)
    assert retention(state, NOW) == 1
    assert retention(state, NOW + timedelta(days=1)) == pytest.approx(0.8)
    assert effective_mastery(state, NOW + timedelta(days=1)) == pytest.approx(0.64)
    assert urgency(state, NOW + timedelta(days=1)) == 0.7
    assert urgency(state, NOW + timedelta(days=10)) == 1
    assert retention(state, NOW - timedelta(days=1)) == 1


def test_difficulty_and_spacing_change_mastery_gains(db):
    easy = db.get(Mastery, "complexity")
    hard = db.get(Mastery, "vectors")
    update_mastery(easy, "answer", 0.1, NOW, correct=True)
    update_mastery(hard, "answer", 0.8, NOW, correct=True)
    assert hard.mastery > easy.mastery
    before = easy.mastery
    update_mastery(easy, "answer", 0.1, NOW + timedelta(minutes=1), correct=True)
    assert easy.mastery - before < before / 3


def test_prerequisites_block_and_then_unlock_after_retrieval(db):
    state = db.get(Mastery, "complexity")
    dependencies = {"binary_search": ["complexity"]}
    assert prerequisite_readiness("binary_search", dependencies, {"complexity": state}, NOW) == 0
    before = select_feed(db, NOW, 4, concept_id="binary_search", seed=7)
    assert all(card.concept_id == "complexity" for card, _ in before)
    update_mastery(state, "answer", 0.2, NOW, correct=True)
    after = select_feed(db, NOW, 4, concept_id="binary_search", seed=7)
    assert all(card.concept_id == "binary_search" for card, _ in after)


def test_multiple_prerequisites_use_weakest_link(db):
    a = db.get(Mastery, "complexity")
    b = db.get(Mastery, "recursion")
    a.mastery = 0.9
    b.mastery = 0.1
    assert (
        prerequisite_readiness(
            "merge_sort", {"merge_sort": ["complexity", "recursion"]}, {"complexity": a, "recursion": b}, NOW
        )
        == 0.1
    )


def test_feed_is_deterministic_and_varied(db):
    first = select_feed(db, NOW, 6, seed=123)
    second = select_feed(db, NOW, 6, seed=123)
    assert [c.id for c, _ in first] == [c.id for c, _ in second]
    assert [r.reason for _, r in first] == [r.reason for _, r in second]
    assert len({c.id for c, _ in first}) == 6
    assert len({c.concept_id for c, _ in first}) >= 3
    assert first[0][0].type == "micro_lesson"
    assert all("score" in r.reason and "weights" in r.reason for _, r in first)


def test_exclusion_and_recycling_never_repeat_active_card(db):
    first = select_feed(db, NOW, 4)
    ids = [c.id for c, _ in first]
    second = select_feed(db, NOW, 4, exclude=ids)
    assert not {c.id for c, _ in second} & set(ids)
    all_ids = list(db.scalars(select(LearningCard.id)).all())
    active = ids[0]
    result = select_feed(db, NOW, 4, exclude=[i for i in all_ids if i != active] + [active])
    assert result
    assert all(c.id != active for c, _ in result)


def test_due_review_outscores_same_non_due_question(db):
    card = db.scalar(
        select(LearningCard).where(LearningCard.concept_id == "complexity", LearningCard.type == "quiz")
    )
    state = db.get(Mastery, "complexity")
    state.times_seen = 3
    not_due = score_candidate(card, state, NOW, 1, 2, [], [], [], DEFAULT_WEIGHTS, random.Random(1))
    state.next_review = NOW - timedelta(days=2)
    state.last_reviewed = NOW - timedelta(days=3)
    state.interval_days = 1
    due = score_candidate(card, state, NOW, 1, 2, [], [], [], DEFAULT_WEIGHTS, random.Random(1))
    assert due["score"] > not_due["score"] + 2
    assert due["is_review"]
    selected = select_feed(db, NOW, 1, seed=1)
    assert selected[0][0].concept_id == "complexity"
    assert selected[0][0].type in ("quiz", "challenge")


def test_repetition_penalty_reduces_score(db):
    card = db.scalar(select(LearningCard).where(LearningCard.concept_id == "vectors"))
    state = db.get(Mastery, "vectors")
    fresh = score_candidate(card, state, NOW, 1, 1, [], [], [], DEFAULT_WEIGHTS, random.Random(1))
    repeat = score_candidate(
        card,
        state,
        NOW,
        1,
        1,
        [card.id],
        [card.concept_id] * 3,
        [card.type] * 3,
        DEFAULT_WEIGHTS,
        random.Random(1),
    )
    assert repeat["score"] < fresh["score"] - 2


def test_reviews_only_requires_encountered_concept(db):
    assert select_feed(db, NOW, reviews_only=True) == []
    db.get(Mastery, "complexity").times_seen = 1
    selected = select_feed(db, NOW, reviews_only=True)
    assert selected
    assert all(c.type in ("quiz", "challenge") and c.concept_id == "complexity" for c, _ in selected)
