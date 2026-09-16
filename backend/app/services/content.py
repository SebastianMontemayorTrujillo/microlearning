import hashlib
import json

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import (
    Concept,
    ConceptDependency,
    LearningCard,
    LearningPath,
    Mastery,
    Question,
    Subject,
    Topic,
)
from app.schemas import CardData, KnowledgeMap


def fingerprint(value) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def store_card(db: Session, data: CardData, source: str = "ai") -> LearningCard:
    if db.get(Concept, data.concept_id) is None:
        raise ValueError("Card references an unknown concept")
    body = data.model_dump()
    digest = fingerprint(body)
    existing = db.scalar(select(LearningCard).where(LearningCard.fingerprint == digest))
    if existing:
        return existing
    # Keep correct answers in the questions table; API responses redact them until submission.
    quiz = body.pop("quiz")
    card = LearningCard(
        concept_id=data.concept_id,
        type=data.type,
        title=data.title,
        content=body,
        source=source,
        fingerprint=digest,
    )
    db.add(card)
    db.flush()
    if quiz:
        db.add(
            Question(
                card_id=card.id,
                prompt=quiz["question"],
                answers=quiz["answers"],
                correct=quiz["correct"],
                explanation=quiz["explanation"],
            )
        )
    return card


def store_map(db: Session, data: KnowledgeMap, subject: Subject) -> list[str]:
    namespace = subject.id + "_"
    existing = db.scalars(select(Concept).join(Topic).where(Topic.subject_id == subject.id)).all()
    if existing:
        return [c.id for c in existing]
    topics: dict[str, Topic] = {}
    for item in data.concepts:
        if item.topic not in topics:
            topic = Topic(id=f"{subject.id}_{len(topics)}", name=item.topic, subject_id=subject.id)
            db.add(topic)
            db.flush()
            topics[item.topic] = topic
        concept = Concept(
            id=namespace + item.id,
            topic_id=topics[item.topic].id,
            name=item.name,
            summary=item.summary,
            difficulty=item.difficulty,
        )
        db.add(concept)
        db.flush()
        db.add(Mastery(concept_id=concept.id))
    db.flush()
    for item in data.concepts:
        for parent in item.prerequisites:
            db.add(ConceptDependency(concept_id=namespace + item.id, prerequisite_id=namespace + parent))
    ordered: list[str] = []

    def visit(item):
        for parent in item.prerequisites:
            visit(next(c for c in data.concepts if c.id == parent))
        full_id = namespace + item.id
        if full_id not in ordered:
            ordered.append(full_id)

    for item in data.concepts:
        visit(item)
    db.add(
        LearningPath(
            subject_id=subject.id,
            title=subject.name,
            description="Your personal path, from foundations to deeper understanding.",
            concept_ids=ordered,
        )
    )
    return ordered
