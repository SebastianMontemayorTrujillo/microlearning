from datetime import datetime

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Interaction, LearningCard, Mastery, Question, Recommendation, Review
from app.schemas import EventInput
from app.services.mastery import update_mastery
from app.services.presentation import mastery_json


def record_event(db: Session, event: EventInput, now: datetime) -> dict:
    decision = db.get(Recommendation, event.presentation_id)
    if decision is None:
        raise HTTPException(404, "Card presentation not found. Refresh your feed.")
    card = db.get(LearningCard, decision.card_id)
    assert card is not None
    state = db.get(Mastery, card.concept_id)
    assert state is not None
    existing = db.scalar(
        select(Interaction).where(Interaction.presentation_id == decision.id, Interaction.kind == event.kind)
    )
    if existing:
        return {"mastery": mastery_json(state, now), **existing.data, "duplicate": True}
    question = db.scalar(select(Question).where(Question.card_id == card.id))
    data: dict = {"seconds": event.seconds}
    correct: bool | None = None
    if event.kind == "answer":
        if question is None or event.answer is None or event.answer >= len(question.answers):
            raise HTTPException(422, "Choose one of this card's answers.")
        correct = event.answer == question.correct
        data.update(
            answer=event.answer,
            correct=correct,
            correct_answer=question.correct,
            explanation=question.explanation,
        )
    before = state.mastery
    update_mastery(state, event.kind, card.content["difficulty"], now, correct, event.seconds)
    interaction = Interaction(
        presentation_id=decision.id,
        card_id=card.id,
        concept_id=card.concept_id,
        kind=event.kind,
        data=data,
        created_at=now,
    )
    db.add(interaction)
    db.flush()
    if correct is not None:
        db.add(
            Review(
                concept_id=card.concept_id,
                interaction_id=interaction.id,
                correct=correct,
                mastery_before=before,
                mastery_after=state.mastery,
                interval_days=state.interval_days,
                scheduled_for=state.next_review,
                created_at=now,
            )
        )
    return {"mastery": mastery_json(state, now), **data, "duplicate": False}
