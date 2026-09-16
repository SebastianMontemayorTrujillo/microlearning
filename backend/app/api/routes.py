import hashlib
import math
import re
from datetime import timedelta, timezone
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Body, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.config import config
from app.db import get_db, write_lock
from app.models import (
    AIGeneration,
    Concept,
    ConceptDependency,
    ImportedDocument,
    Interaction,
    LearningCard,
    LearningPath,
    Mastery,
    Recommendation,
    SavedCard,
    Subject,
    Topic,
    uid,
    utcnow,
)
from app.schemas import CardData, EventInput, ImportInput, OnboardingInput, PreferencesInput, TutorInput
from app.services.ai_service import AIService, AIUnavailable
from app.services.content import store_card
from app.services.interactions import record_event
from app.services.mastery import effective_mastery, is_mastered
from app.services.presentation import card_json, iso, mastery_json
from app.services.recommender import (
    PREREQUISITE_THRESHOLD,
    next_path_concept,
    prerequisite_readiness,
    select_feed,
)
from app.services.settings import DEFAULT_SETTINGS, DEFAULT_WEIGHTS, get_setting, set_setting

router = APIRouter(prefix="/api")


@router.get("/health")
def health(db: Session = Depends(get_db)):
    db.execute(select(1))
    return {"status": "ok", "mode": "ai" if AIService(db).enabled else "demo"}


@router.get("/settings")
def settings(db: Session = Depends(get_db)):
    return {
        **{k: get_setting(db, k) for k in DEFAULT_SETTINGS},
        "ai_available": bool(config.openai_api_key),
        "model": config.openai_model,
        "timezone": config.learning_timezone,
        "subjects": [
            {"id": s.id, "name": s.name, "color": s.color, "selected": s.selected}
            for s in db.scalars(select(Subject).order_by(Subject.name)).all()
        ],
    }


@router.patch("/settings")
def update_settings(data: PreferencesInput, db: Session = Depends(get_db)):
    values = data.model_dump(exclude_none=True)
    if data.weights is not None:
        if set(data.weights) != set(DEFAULT_WEIGHTS) or any(
            not math.isfinite(v) or v < 0 or v > 10 for v in data.weights.values()
        ):
            raise HTTPException(422, "Provide all recommendation weights, each between 0 and 10.")
    with write_lock:
        for key, value in values.items():
            set_setting(db, key, value)
        db.commit()
    return settings(db)


@router.post("/onboarding")
def onboard(data: OnboardingInput, db: Session = Depends(get_db)):
    with write_lock:
        existing = list(db.scalars(select(Subject)).all())
        names = {s.name.casefold(): s for s in existing}
        for subject in existing:
            subject.selected = subject.name.casefold() in {n.casefold() for n in data.subjects}
        for name in data.subjects:
            if name.casefold() not in names:
                subject = Subject(id=uid(), name=name, color="peach", selected=True)
                db.add(subject)
                names[name.casefold()] = subject
        # Level is only a low-confidence prior on never-encountered concepts.
        prior = {"beginner": 0.0, "intermediate": 0.1, "advanced": 0.2}[data.level]
        for state in db.scalars(
            select(Mastery).where(
                Mastery.times_seen == 0, Mastery.correct_answers == 0, Mastery.incorrect_answers == 0
            )
        ).all():
            state.mastery = prior
            state.confidence = 0.03 if prior else 0.0
        set_setting(db, "level", data.level)
        set_setting(db, "onboarded", True)
        db.commit()
    return settings(db)


@router.get("/feed")
def feed(
    limit: int = Query(4, ge=1, le=10),
    exclude: str = Query("", max_length=6000),
    subject_id: str | None = Query(None, max_length=100),
    concept_id: str | None = Query(None, max_length=100),
    mode: str = Query("for-you", pattern="^(for-you|reviews)$"),
    db: Session = Depends(get_db),
):
    now = utcnow()
    with write_lock:
        count = db.scalar(select(func.count(Interaction.id))) or 0
        decisions = select_feed(
            db,
            now,
            limit,
            exclude.split(",")[-60:] if exclude else [],
            seed=int(now.strftime("%Y%m%d")) + count,
            subject_id=subject_id,
            concept_id=concept_id,
            reviews_only=mode == "reviews",
        )
        db.commit()
        cards = [card_json(db, card, now, decision) for card, decision in decisions]
    return {"cards": cards, "mode": "ai" if AIService(db).enabled else "demo"}


@router.post("/interactions")
def interact(data: EventInput, db: Session = Depends(get_db)):
    with write_lock:
        result = record_event(db, data, utcnow())
        db.commit()
    return result


@router.get("/saved")
def saved(db: Session = Depends(get_db)):
    cards = db.scalars(select(LearningCard).join(SavedCard).order_by(SavedCard.created_at.desc())).all()
    return {"cards": [card_json(db, card, utcnow()) for card in cards]}


@router.put("/cards/{card_id}/saved")
def save_card(card_id: str, saved: bool = Body(embed=True), db: Session = Depends(get_db)):
    with write_lock:
        if db.get(LearningCard, card_id) is None:
            raise HTTPException(404, "Card not found")
        existing = db.get(SavedCard, card_id)
        if saved and existing is None:
            db.add(SavedCard(card_id=card_id))
        elif not saved and existing:
            db.delete(existing)
        db.commit()
    return {"saved": saved}


@router.post("/cards/{card_id}/open")
def open_card(card_id: str, db: Session = Depends(get_db)):
    card = db.get(LearningCard, card_id)
    if card is None:
        raise HTTPException(404, "Card not found")
    with write_lock:
        decision = Recommendation(
            card_id=card.id, reason={"label": "You chose to revisit this card", "is_review": False}
        )
        db.add(decision)
        db.commit()
    return card_json(db, card, utcnow(), decision)


@router.get("/knowledge")
def knowledge(db: Session = Depends(get_db)):
    now = utcnow()
    states = {m.concept_id: m for m in db.scalars(select(Mastery)).all()}
    dependencies: dict[str, list[str]] = {}
    for d in db.scalars(select(ConceptDependency)).all():
        dependencies.setdefault(d.concept_id, []).append(d.prerequisite_id)
    concepts = [
        {
            "id": c.id,
            "topic_id": c.topic_id,
            "name": c.name,
            "summary": c.summary,
            "difficulty": c.difficulty,
            "prerequisites": dependencies.get(c.id, []),
            "unlocked": prerequisite_readiness(c.id, dependencies, states, now) >= PREREQUISITE_THRESHOLD,
            "mastery": mastery_json(states[c.id], now),
            "mastered": is_mastered(states[c.id], now),
        }
        for c in db.scalars(select(Concept)).all()
    ]
    return {
        "subjects": settings(db)["subjects"],
        "topics": [
            {"id": t.id, "subject_id": t.subject_id, "name": t.name} for t in db.scalars(select(Topic)).all()
        ],
        "concepts": concepts,
        "paths": [
            {
                "id": p.id,
                "subject_id": p.subject_id,
                "title": p.title,
                "description": p.description,
                "concept_ids": p.concept_ids,
                "next_concept_id": next_path_concept(p.concept_ids, dependencies, states, now),
                "progress": sum(
                    effective_mastery(states[c], now) if states[c].times_seen else 0 for c in p.concept_ids
                )
                / max(1, len(p.concept_ids)),
            }
            for p in db.scalars(select(LearningPath)).all()
        ],
    }


@router.get("/progress")
def progress(db: Session = Depends(get_db)):
    now = utcnow()
    graph = knowledge(db)
    states = list(db.scalars(select(Mastery)).all())
    encountered = [s for s in states if s.times_seen > 0]
    mastered = [s for s in encountered if is_mastered(s, now)]
    due = [s for s in encountered if s.next_review and s.next_review <= now]
    zone = ZoneInfo(config.learning_timezone)
    today = now.replace(tzinfo=timezone.utc).astimezone(zone).date()
    interactions = db.scalars(select(Interaction).where(Interaction.kind.in_(["dwell", "answer"]))).all()
    active_days = set()
    seconds_by_day: dict[str, float] = {}
    for event in interactions:
        day = event.created_at.replace(tzinfo=timezone.utc).astimezone(zone).date()
        if event.kind == "answer" or event.data.get("seconds", 0) >= 12:
            active_days.add(day)
        if event.kind == "dwell":
            seconds_by_day[day.isoformat()] = seconds_by_day.get(day.isoformat(), 0) + event.data.get(
                "seconds", 0
            )
    streak = 0
    day = today if today in active_days else today - timedelta(days=1)
    while day in active_days:
        streak += 1
        day -= timedelta(days=1)
    subjects = []
    for subject in graph["subjects"]:
        topics = [t["id"] for t in graph["topics"] if t["subject_id"] == subject["id"]]
        members = [c for c in graph["concepts"] if c["topic_id"] in topics]
        subjects.append(
            {
                **subject,
                "mastery": sum(
                    c["mastery"]["effective_mastery"] if c["mastery"]["times_seen"] else 0 for c in members
                )
                / max(1, len(members)),
                "concept_count": len(members),
            }
        )
    topic_progress = []
    for topic in graph["topics"]:
        members = [c for c in graph["concepts"] if c["topic_id"] == topic["id"]]
        topic_progress.append(
            {
                **topic,
                "mastery": sum(
                    c["mastery"]["effective_mastery"] if c["mastery"]["times_seen"] else 0 for c in members
                )
                / max(1, len(members)),
            }
        )
    week = [
        {
            "date": (today - timedelta(days=i)).isoformat(),
            "day": (today - timedelta(days=i)).strftime("%a"),
            "minutes": round(seconds_by_day.get((today - timedelta(days=i)).isoformat(), 0) / 60, 1),
        }
        for i in range(6, -1, -1)
    ]
    return {
        "encountered": len(encountered),
        "mastered": len(mastered),
        "reviews_due": len(due),
        "streak": streak,
        "total_minutes": round(sum(seconds_by_day.values()) / 60, 1),
        "today_minutes": round(seconds_by_day.get(today.isoformat(), 0) / 60, 1),
        "week": week,
        "subjects": subjects,
        "topics": topic_progress,
        "total_concepts": len(states),
        "recent": [
            s.concept_id for s in sorted(encountered, key=lambda s: s.last_seen or now, reverse=True)[:6]
        ],
        "weak": [s.concept_id for s in sorted(encountered, key=lambda s: effective_mastery(s, now))[:5]],
        "due": [s.concept_id for s in due],
    }


@router.post("/tutor")
def tutor(data: TutorInput, db: Session = Depends(get_db)):
    card = db.get(LearningCard, data.card_id)
    if card is None:
        raise HTTPException(404, "Card not found")
    try:
        result, mode = AIService(db).explainConcept(card, data.message, data.history)
        return {**result.model_dump(), "mode": mode}
    except AIUnavailable as exc:
        raise HTTPException(503, str(exc)) from exc


@router.get("/usage")
def usage(db: Session = Depends(get_db)):
    rows = db.scalars(select(AIGeneration).order_by(AIGeneration.created_at.desc())).all()
    today = utcnow().date()
    seen = select(Interaction.card_id).where(Interaction.kind == "shown").distinct()
    return {
        "enabled": AIService(db).enabled,
        "model": config.openai_model,
        "daily_budget": config.ai_daily_budget_usd,
        "today_cost": sum(r.estimated_cost for r in rows if r.created_at.date() == today),
        "total_cost": sum(r.estimated_cost for r in rows),
        "input_tokens": sum(r.input_tokens for r in rows),
        "output_tokens": sum(r.output_tokens for r in rows),
        "cache_hits": get_setting(db, "cache_hits") or 0,
        "buffer_available": db.scalar(select(func.count(LearningCard.id)).where(~LearningCard.id.in_(seen)))
        or 0,
        "total_cards": db.scalar(select(func.count(LearningCard.id))) or 0,
        "generated_cards": db.scalar(select(func.count(LearningCard.id)).where(LearningCard.source == "ai"))
        or 0,
        "recent": [
            {
                "id": r.id,
                "kind": r.kind,
                "status": r.status,
                "model": r.model,
                "input_tokens": r.input_tokens,
                "output_tokens": r.output_tokens,
                "estimated_cost": r.estimated_cost,
                "error": r.error,
                "created_at": iso(r.created_at),
            }
            for r in rows[:20]
        ],
    }


@router.get("/imports")
def imports(db: Session = Depends(get_db)):
    return {
        "documents": [
            {"id": d.id, "title": d.title, "status": d.status, "created_at": iso(d.created_at)}
            for d in db.scalars(select(ImportedDocument).order_by(ImportedDocument.created_at.desc())).all()
        ]
    }


@router.post("/imports")
def import_document(data: ImportInput, db: Session = Depends(get_db)):
    digest = hashlib.sha256(data.text.strip().encode()).hexdigest()
    with write_lock:
        previous = db.scalar(select(ImportedDocument).where(ImportedDocument.fingerprint == digest))
        if previous:
            return {"id": previous.id, "status": previous.status, "duplicate": True}
        subject = Subject(id=uid(), name=f"{data.title[:80]} · {digest[:6]}", color="peach", selected=True)
        db.add(subject)
        db.flush()
        document = ImportedDocument(
            title=data.title, text=data.text, fingerprint=digest, subject_id=subject.id
        )
        db.add(document)
        db.flush()
        if not AIService(db).enabled:
            # Local import is honest excerpt-based study, not an invented AI analysis.
            topic = Topic(id=uid(), subject_id=subject.id, name="Your notes")
            db.add(topic)
            db.flush()
            chunks = [chunk.strip() for chunk in re.split(r"\n\s*\n", data.text) if len(chunk.strip()) >= 30]
            if not chunks:
                chunks = [data.text]
            bounded = [
                chunk[i : i + 1800]
                for chunk in chunks
                for i in range(0, len(chunk), 1800)
                if len(chunk[i : i + 1800]) >= 30
            ][:24]
            concept_ids = []
            for index, text in enumerate(bounded):
                concept = Concept(
                    id=uid(),
                    topic_id=topic.id,
                    name=f"{data.title[:100]} · passage {index + 1}",
                    summary=text,
                    difficulty=0.3,
                )
                db.add(concept)
                db.flush()
                db.add(Mastery(concept_id=concept.id))
                concept_ids.append(concept.id)
                for kind in ("micro_lesson", "flashcard"):
                    store_card(
                        db,
                        CardData(
                            concept_id=concept.id,
                            type=kind,
                            title=concept.name,
                            hook="Read this passage, then explain its main idea in your own words."
                            if kind == "micro_lesson"
                            else "What is the main idea of this passage? Recall before revealing.",
                            explanation=text,
                            takeaway="Compare your explanation with the original passage. This card uses your source text verbatim.",
                            difficulty=0.3,
                            estimated_seconds=60,
                            steps=[],
                            equation=None,
                            code=None,
                            visualization=None,
                            quiz=None,
                        ),
                        "notes",
                    )
            db.add(
                LearningPath(
                    subject_id=subject.id,
                    title=data.title,
                    description="Study excerpts from your own notes. Passage order is preserved; prerequisites have not been inferred.",
                    concept_ids=concept_ids,
                )
            )
            document.status = "local_excerpts"
        db.commit()
        return {"id": document.id, "status": document.status, "duplicate": False}
