import asyncio
import logging

from sqlalchemy import func, select

from app.config import config
from app.db import SessionLocal, write_lock
from app.models import (
    Concept,
    ConceptDependency,
    ImportedDocument,
    Interaction,
    LearningCard,
    Mastery,
    Subject,
    Topic,
    utcnow,
)
from app.services.ai_service import AIService, AIUnavailable
from app.services.content import store_card, store_map
from app.services.recommender import PREREQUISITE_THRESHOLD, prerequisite_readiness
from app.services.settings import get_setting

logger = logging.getLogger(__name__)


def replenish_once() -> None:
    with SessionLocal() as db:
        ai = AIService(db)
        if not ai.enabled or not get_setting(db, "onboarded"):
            return
        for subject in db.scalars(select(Subject).where(Subject.selected.is_(True))).all():
            exists = db.scalar(select(Concept.id).join(Topic).where(Topic.subject_id == subject.id).limit(1))
            if not exists:
                document = db.scalar(
                    select(ImportedDocument).where(ImportedDocument.subject_id == subject.id)
                )
                data = ai.generateKnowledgeMap(
                    [subject.name], get_setting(db, "level"), document.text if document else None
                )
                with write_lock:
                    store_map(db, data, subject)
                    if document:
                        document.status = "mapped"
                    db.commit()
                return
        selected_concepts = list(
            db.scalars(select(Concept).join(Topic).join(Subject).where(Subject.selected.is_(True))).all()
        )
        if not selected_concepts:
            return
        states = {m.concept_id: m for m in db.scalars(select(Mastery)).all()}
        dependencies: dict[str, list[str]] = {}
        for dependency in db.scalars(select(ConceptDependency)).all():
            dependencies.setdefault(dependency.concept_id, []).append(dependency.prerequisite_id)
        eligible_concepts = [
            c
            for c in selected_concepts
            if prerequisite_readiness(c.id, dependencies, states, utcnow()) >= PREREQUISITE_THRESHOLD
        ]
        seen = select(Interaction.card_id).where(Interaction.kind == "shown").distinct()
        available = int(
            db.scalar(
                select(func.count(LearningCard.id)).where(
                    LearningCard.concept_id.in_([c.id for c in eligible_concepts]), ~LearningCard.id.in_(seen)
                )
            )
            or 0
        )
        generated = db.scalar(select(LearningCard.id).where(LearningCard.source == "ai").limit(1))
        counts: dict[str, int] = {
            cid: count
            for cid, count in db.execute(
                select(LearningCard.concept_id, func.count(LearningCard.id)).group_by(LearningCard.concept_id)
            ).all()
        }
        empty = [c for c in selected_concepts if not counts.get(c.id)]
        if available >= config.content_buffer_low and generated and not empty:
            # A refill cycle continues to target across ticks, then goes back to the low-water trigger.
            if not get_setting(db, "refilling"):
                return
        if available >= config.content_buffer_target and generated and not empty:
            from app.services.settings import set_setting

            with write_lock:
                set_setting(db, "refilling", False)
                db.commit()
            return
        from app.services.settings import set_setting

        with write_lock:
            set_setting(db, "refilling", True)
            db.commit()
        candidates = sorted(
            empty or eligible_concepts, key=lambda c: (counts.get(c.id, 0), c.difficulty, c.id)
        )[:3]
        if not candidates:
            return
        candidate_ids = {c.id for c in candidates}
        titles = list(
            db.scalars(
                select(LearningCard.title)
                .where(LearningCard.concept_id.in_(candidate_ids))
                .order_by(LearningCard.created_at)
            ).all()
        )
        topic = db.get(Topic, candidates[0].topic_id)
        document = (
            db.scalar(select(ImportedDocument).where(ImportedDocument.subject_id == topic.subject_id))
            if topic
            else None
        )
        batch = ai.generateLessons(
            [
                {
                    "id": c.id,
                    "name": c.name,
                    "summary": c.summary,
                    "difficulty": c.difficulty,
                    "mastery": states[c.id].mastery,
                }
                for c in candidates
            ],
            config.ai_batch_size,
            titles,
            document.text if document else None,
        )
        if any(c.concept_id not in candidate_ids for c in batch.cards):
            raise ValueError("Generated batch references concepts outside its requested scope")
        with write_lock:
            for card in batch.cards:
                store_card(db, card)
            if document:
                document.status = "ready"
            db.commit()
        logger.info("Content buffer: stored batch of %d cards", len(batch.cards))


async def buffer_worker() -> None:
    while True:
        try:
            await asyncio.to_thread(replenish_once)
        except AIUnavailable as exc:
            logger.info("Content buffer paused: %s", exc)
        except Exception as exc:
            logger.warning("Content buffer error (%s)", type(exc).__name__)
        await asyncio.sleep(30)
