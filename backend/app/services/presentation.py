from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Concept, LearningCard, Mastery, Question, Recommendation, SavedCard, Subject, Topic
from app.services.mastery import effective_mastery
from app.services.spaced_repetition import retention


def iso(value: datetime | None) -> str | None:
    return value.isoformat() + "Z" if value else None


def mastery_json(state: Mastery, now: datetime) -> dict:
    return {
        "concept_id": state.concept_id,
        "mastery": round(state.mastery, 4),
        "effective_mastery": round(effective_mastery(state, now), 4),
        "confidence": round(state.confidence, 4),
        "retention": round(retention(state, now), 4),
        "times_seen": state.times_seen,
        "correct_answers": state.correct_answers,
        "incorrect_answers": state.incorrect_answers,
        "last_reviewed": iso(state.last_reviewed),
        "next_review": iso(state.next_review),
        "interval_days": state.interval_days,
        "retrieval_streak": state.retrieval_streak,
    }


def card_json(db: Session, card: LearningCard, now: datetime, decision: Recommendation | None = None) -> dict:
    concept = db.get(Concept, card.concept_id)
    assert concept is not None
    topic = db.get(Topic, concept.topic_id)
    assert topic is not None
    subject = db.get(Subject, topic.subject_id)
    state = db.get(Mastery, concept.id)
    assert subject is not None and state is not None
    question = db.scalar(select(Question).where(Question.card_id == card.id))
    return {
        "id": card.id,
        **card.content,
        "source": card.source,
        "concept_name": concept.name,
        "subject": subject.name,
        "subject_id": subject.id,
        "topic": topic.name,
        "color": subject.color,
        "quiz": {"question": question.prompt, "answers": question.answers} if question else None,
        "saved": db.get(SavedCard, card.id) is not None,
        "mastery": mastery_json(state, now),
        "presentation_id": decision.id if decision else None,
        "recommendation_reason": decision.reason if decision else None,
    }
