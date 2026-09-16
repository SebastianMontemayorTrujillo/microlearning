from datetime import datetime
from typing import Any
from uuid import uuid4

from sqlalchemy import JSON, Boolean, DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


def uid() -> str:
    return str(uuid4())


def utcnow() -> datetime:
    # All persisted timestamps are naive UTC, portable across SQLite and PostgreSQL.
    return datetime.now(__import__("datetime").timezone.utc).replace(tzinfo=None)


class Subject(Base):
    __tablename__ = "subjects"
    id: Mapped[str] = mapped_column(String(100), primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True)
    color: Mapped[str] = mapped_column(String(30), default="mint")
    selected: Mapped[bool] = mapped_column(Boolean, default=True)


class Topic(Base):
    __tablename__ = "topics"
    id: Mapped[str] = mapped_column(String(100), primary_key=True)
    subject_id: Mapped[str] = mapped_column(ForeignKey("subjects.id"), index=True)
    name: Mapped[str] = mapped_column(String(150))


class Concept(Base):
    __tablename__ = "concepts"
    id: Mapped[str] = mapped_column(String(100), primary_key=True)
    topic_id: Mapped[str] = mapped_column(ForeignKey("topics.id"), index=True)
    name: Mapped[str] = mapped_column(String(200))
    summary: Mapped[str] = mapped_column(Text)
    difficulty: Mapped[float] = mapped_column(Float, default=0.3)


class ConceptDependency(Base):
    __tablename__ = "concept_dependencies"
    concept_id: Mapped[str] = mapped_column(ForeignKey("concepts.id"), primary_key=True)
    prerequisite_id: Mapped[str] = mapped_column(ForeignKey("concepts.id"), primary_key=True)


class LearningCard(Base):
    __tablename__ = "learning_cards"
    id: Mapped[str] = mapped_column(String(100), primary_key=True, default=uid)
    concept_id: Mapped[str] = mapped_column(ForeignKey("concepts.id"), index=True)
    type: Mapped[str] = mapped_column(String(30))
    title: Mapped[str] = mapped_column(String(200))
    content: Mapped[dict[str, Any]] = mapped_column(JSON)
    source: Mapped[str] = mapped_column(String(30), default="seed")
    fingerprint: Mapped[str] = mapped_column(String(64), unique=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)


class Question(Base):
    __tablename__ = "questions"
    id: Mapped[str] = mapped_column(String(100), primary_key=True, default=uid)
    card_id: Mapped[str] = mapped_column(ForeignKey("learning_cards.id"), unique=True)
    prompt: Mapped[str] = mapped_column(Text)
    answers: Mapped[list[str]] = mapped_column(JSON)
    correct: Mapped[int] = mapped_column(Integer)
    explanation: Mapped[str] = mapped_column(Text)


class Mastery(Base):
    __tablename__ = "user_concept_mastery"
    concept_id: Mapped[str] = mapped_column(ForeignKey("concepts.id"), primary_key=True)
    mastery: Mapped[float] = mapped_column(Float, default=0.0)
    confidence: Mapped[float] = mapped_column(Float, default=0.0)
    interest: Mapped[float] = mapped_column(Float, default=0.5)
    times_seen: Mapped[int] = mapped_column(Integer, default=0)
    correct_answers: Mapped[int] = mapped_column(Integer, default=0)
    incorrect_answers: Mapped[int] = mapped_column(Integer, default=0)
    retrieval_streak: Mapped[int] = mapped_column(Integer, default=0)
    interval_days: Mapped[float] = mapped_column(Float, default=0)
    last_seen: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    last_reviewed: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    last_retrieval: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    next_review: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, index=True)


class Recommendation(Base):
    __tablename__ = "recommendations"
    id: Mapped[str] = mapped_column(String(100), primary_key=True, default=uid)
    card_id: Mapped[str] = mapped_column(ForeignKey("learning_cards.id"), index=True)
    reason: Mapped[dict[str, Any]] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)


class Interaction(Base):
    __tablename__ = "interactions"
    __table_args__ = (UniqueConstraint("presentation_id", "kind"),)
    id: Mapped[str] = mapped_column(String(100), primary_key=True, default=uid)
    presentation_id: Mapped[str] = mapped_column(ForeignKey("recommendations.id"), index=True)
    card_id: Mapped[str] = mapped_column(ForeignKey("learning_cards.id"), index=True)
    concept_id: Mapped[str] = mapped_column(ForeignKey("concepts.id"), index=True)
    kind: Mapped[str] = mapped_column(String(30))
    data: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, index=True)


class Review(Base):
    __tablename__ = "reviews"
    id: Mapped[str] = mapped_column(String(100), primary_key=True, default=uid)
    concept_id: Mapped[str] = mapped_column(ForeignKey("concepts.id"), index=True)
    interaction_id: Mapped[str] = mapped_column(ForeignKey("interactions.id"), unique=True)
    correct: Mapped[bool] = mapped_column(Boolean)
    mastery_before: Mapped[float] = mapped_column(Float)
    mastery_after: Mapped[float] = mapped_column(Float)
    interval_days: Mapped[float] = mapped_column(Float)
    scheduled_for: Mapped[datetime] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)


class SavedCard(Base):
    __tablename__ = "saved_cards"
    card_id: Mapped[str] = mapped_column(ForeignKey("learning_cards.id"), primary_key=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)


class LearningPath(Base):
    __tablename__ = "learning_paths"
    id: Mapped[str] = mapped_column(String(100), primary_key=True, default=uid)
    subject_id: Mapped[str] = mapped_column(ForeignKey("subjects.id"), index=True)
    title: Mapped[str] = mapped_column(String(200))
    description: Mapped[str] = mapped_column(Text)
    concept_ids: Mapped[list[str]] = mapped_column(JSON)


class AIGeneration(Base):
    __tablename__ = "ai_generations"
    id: Mapped[str] = mapped_column(String(100), primary_key=True, default=uid)
    kind: Mapped[str] = mapped_column(String(30))
    model: Mapped[str] = mapped_column(String(100))
    cache_key: Mapped[str] = mapped_column(String(64), unique=True)
    status: Mapped[str] = mapped_column(String(30), default="pending")
    result: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    input_tokens: Mapped[int] = mapped_column(Integer, default=0)
    output_tokens: Mapped[int] = mapped_column(Integer, default=0)
    estimated_cost: Mapped[float] = mapped_column(Float, default=0)
    error: Mapped[str | None] = mapped_column(String(200), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, index=True)


class Setting(Base):
    __tablename__ = "settings"
    key: Mapped[str] = mapped_column(String(100), primary_key=True)
    value: Mapped[Any] = mapped_column(JSON)


class ImportedDocument(Base):
    __tablename__ = "imported_documents"
    id: Mapped[str] = mapped_column(String(100), primary_key=True, default=uid)
    title: Mapped[str] = mapped_column(String(200))
    text: Mapped[str] = mapped_column(Text)
    fingerprint: Mapped[str] = mapped_column(String(64), unique=True)
    status: Mapped[str] = mapped_column(String(30), default="stored")
    subject_id: Mapped[str | None] = mapped_column(ForeignKey("subjects.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
