import random
from collections import Counter
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import (
    Concept,
    ConceptDependency,
    Interaction,
    LearningCard,
    Mastery,
    Recommendation,
    Subject,
    Topic,
)
from app.services.mastery import effective_mastery, is_mastered
from app.services.settings import DEFAULT_WEIGHTS, get_setting
from app.services.spaced_repetition import urgency

PREREQUISITE_THRESHOLD = 0.25


def next_path_concept(
    ids: list[str], dependencies: dict[str, list[str]], states: dict[str, Mastery], now: datetime
) -> str | None:
    eligible = [
        cid for cid in ids if prerequisite_readiness(cid, dependencies, states, now) >= PREREQUISITE_THRESHOLD
    ]
    for cid in eligible:
        if not is_mastered(states[cid], now):
            return cid
    return (
        min(eligible, key=lambda cid: effective_mastery(states[cid], now))
        if eligible
        else (ids[0] if ids else None)
    )


def prerequisite_readiness(
    concept_id: str, dependencies: dict[str, list[str]], states: dict[str, Mastery], now: datetime
) -> float:
    parents = dependencies.get(concept_id, [])
    if not parents:
        return 1.0
    return min(effective_mastery(states[parent], now) if parent in states else 0 for parent in parents)


def score_candidate(
    card: LearningCard,
    state: Mastery,
    now: datetime,
    readiness: float,
    dependent_count: int,
    recent_cards: list[str],
    recent_concepts: list[str],
    recent_types: list[str],
    weights: dict[str, float],
    rng: random.Random,
) -> dict:
    current = effective_mastery(state, now)
    retrieval = card.type in ("quiz", "challenge")
    due = urgency(state, now)
    difficulty = float(card.content["difficulty"])
    recent_count = recent_concepts[-5:].count(card.concept_id)
    components = {
        "learning_value": min(
            1.0,
            (1 - current) * 0.6
            + min(3, dependent_count) * 0.1
            + (0.3 if retrieval and state.times_seen else 0),
        ),
        "review_urgency": due if retrieval else due * 0.12,
        "difficulty_match": max(0.0, 1 - abs(difficulty - min(0.95, current + 0.25)) / 0.75),
        "interest": state.interest,
        "prerequisite_relevance": min(1.0, dependent_count / 3) * (1 - current),
        "novelty": 1.0 if state.times_seen == 0 else 0.3 if card.id not in recent_cards else 0,
        "variety": (0 if recent_types and recent_types[-1] == card.type else 1) * 0.6
        + (0 if recent_concepts and recent_concepts[-1] == card.concept_id else 1) * 0.4,
        "repetition_penalty": min(2.0, recent_count * 0.6 + (1 if card.id in recent_cards[-8:] else 0)),
        "exploration": rng.random(),
    }
    # All unseen concepts begin with teaching, never an unexplained assessment.
    if state.times_seen == 0 and card.type != "micro_lesson":
        components["learning_value"] *= 0.25
        components["novelty"] *= 0.4
    # Ensure due reviews surface, but mix them with teaching after two retrieval cards.
    if len(recent_types) >= 2 and all(t in ("quiz", "challenge") for t in recent_types[-2:]) and retrieval:
        components["variety"] = 0
        components["review_urgency"] *= 0.25
        components["repetition_penalty"] += 0.7
    score = sum(
        value * weights.get(key, DEFAULT_WEIGHTS[key]) * (-1 if key == "repetition_penalty" else 1)
        for key, value in components.items()
    )
    if due >= 0.7 and retrieval:
        label = "Due for a memory refresh"
    elif state.incorrect_answers > state.correct_answers and retrieval:
        label = "Practice a concept that needs another look"
    elif state.times_seen and retrieval:
        label = "Turn understanding into lasting recall"
    elif dependent_count:
        label = "A foundation that unlocks your next concepts"
    elif state.times_seen == 0:
        label = "A new idea at the right level for you"
    else:
        label = "A different angle on something you're learning"
    return {
        **{k: round(v, 4) for k, v in components.items()},
        "score": round(score, 4),
        "prerequisite_readiness": round(readiness, 4),
        "mastery_at_selection": round(current, 4),
        "label": label,
        "is_review": due >= 0.7 and retrieval,
    }


def select_feed(
    db: Session,
    now: datetime,
    limit: int = 4,
    exclude: list[str] | None = None,
    seed: int = 42,
    subject_id: str | None = None,
    concept_id: str | None = None,
    reviews_only: bool = False,
) -> list[tuple[LearningCard, Recommendation]]:
    states = {s.concept_id: s for s in db.scalars(select(Mastery)).all()}
    dependencies: dict[str, list[str]] = {}
    for d in db.scalars(select(ConceptDependency)).all():
        dependencies.setdefault(d.concept_id, []).append(d.prerequisite_id)
    dependents = Counter(p for parents in dependencies.values() for p in parents)
    query = select(LearningCard).join(Concept).join(Topic).join(Subject).where(Subject.selected.is_(True))
    if subject_id:
        query = query.where(Subject.id == subject_id)
    cards = list(db.scalars(query.order_by(LearningCard.id)).all())
    # A path may request a locked concept; follow its missing prerequisites to an eligible foundation.
    focus = concept_id
    visited: set[str] = set()
    while focus and focus not in visited:
        visited.add(focus)
        missing = [
            p
            for p in dependencies.get(focus, [])
            if effective_mastery(states[p], now) < PREREQUISITE_THRESHOLD
        ]
        if not missing:
            break
        focus = min(missing, key=lambda p: effective_mastery(states[p], now))
    if focus:
        cards = [c for c in cards if c.concept_id == focus]
    cards = [
        c
        for c in cards
        if prerequisite_readiness(c.concept_id, dependencies, states, now) >= PREREQUISITE_THRESHOLD
    ]
    if reviews_only:
        cards = [c for c in cards if c.type in ("quiz", "challenge") and states[c.concept_id].times_seen > 0]
    history = list(
        db.scalars(
            select(Interaction)
            .where(Interaction.kind == "shown")
            .order_by(Interaction.created_at.desc(), Interaction.id)
            .limit(20)
        ).all()
    )[::-1]
    card_lookup = {c.id: c for c in db.scalars(select(LearningCard)).all()}
    recent_cards = [i.card_id for i in history]
    recent_concepts = [i.concept_id for i in history]
    recent_types = [card_lookup[i.card_id].type for i in history]
    weights = {**DEFAULT_WEIGHTS, **(get_setting(db, "weights") or {})}
    excluded = set(exclude or [])
    rng = random.Random(seed)
    result: list[tuple[LearningCard, Recommendation]] = []
    for _ in range(limit):
        eligible = [c for c in cards if c.id not in excluded]
        if not eligible and not result:
            # Finite cached content can recycle as practice. Never repeat the active card.
            eligible = [c for c in cards if c.id not in set((exclude or [])[-1:])]
        if not eligible:
            break
        ranked = []
        for card in eligible:
            reason = score_candidate(
                card,
                states[card.concept_id],
                now,
                prerequisite_readiness(card.concept_id, dependencies, states, now),
                dependents[card.concept_id],
                recent_cards,
                recent_concepts,
                recent_types,
                weights,
                rng,
            )
            if focus:
                reason["label"] = (
                    "A prerequisite to build first"
                    if focus != concept_id
                    else "The next step on your learning path"
                )
            ranked.append((reason["score"], card.id, card, reason))
        _, _, chosen, reason = max(ranked, key=lambda x: (x[0], x[1]))
        decision = Recommendation(card_id=chosen.id, reason={**reason, "weights": weights, "seed": seed})
        db.add(decision)
        db.flush()
        result.append((chosen, decision))
        excluded.add(chosen.id)
        recent_cards.append(chosen.id)
        recent_concepts.append(chosen.concept_id)
        recent_types.append(chosen.type)
    return result
