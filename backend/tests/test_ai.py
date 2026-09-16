from types import SimpleNamespace

import pytest
from pydantic import ValidationError
from sqlalchemy import func, select

from app.config import config
from app.models import AIGeneration, LearningCard, Subject
from app.schemas import CardBatch, CardData, KnowledgeMap, QuizData, TutorResponse, VisualData
from app.services.ai_service import AIService, AIUnavailable
from app.services.content import store_card, store_map


def valid_card():
    return dict(
        concept_id="complexity",
        type="micro_lesson",
        title="A new perspective on linear work",
        hook="One pass grows with your input.",
        explanation="Checking n items once takes n checks. Two consecutive passes still have linear growth, O(n).",
        takeaway="Count how work grows with input size.",
        difficulty=0.3,
        estimated_seconds=30,
        steps=[],
        equation=None,
        code=None,
        visualization=None,
        quiz=None,
    )


def test_card_schema_rejects_invalid_or_executable_content():
    assert CardData.model_validate(valid_card())
    for changes in [
        {"type": "raw_html"},
        {"difficulty": 2},
        {"type": "quiz"},
        {"type": "visualization"},
        {"html": "<script>alert(1)</script>"},
        {"estimated_seconds": 999},
    ]:
        with pytest.raises(ValidationError):
            CardData.model_validate({**valid_card(), **changes})


def test_quiz_validation():
    good = dict(
        question="How many steps?",
        answers=["One", "Two"],
        correct=1,
        explanation="There are two steps in this example.",
    )
    assert QuizData.model_validate(good)
    for changes in [{"correct": 3}, {"answers": ["One", "One"]}, {"answers": ["", "Two"]}]:
        with pytest.raises(ValidationError):
            QuizData.model_validate({**good, **changes})


def test_visualization_validation():
    with pytest.raises(ValidationError):
        VisualData(type="array_elimination", values=[3, 1, 2], labels=[], caption="Unsorted")
    with pytest.raises(ValidationError):
        VisualData(type="vector", values=[float("nan"), 2], labels=[], caption="Bad coordinate")
    with pytest.raises(ValidationError):
        VisualData(type="vector", values=[1, 2, 3], labels=[], caption="Wrong dimensions")


def concept(cid, parents):
    return {
        "id": cid,
        "name": cid,
        "topic": "Foundations",
        "summary": "A useful foundational concept for this subject.",
        "difficulty": 0.3,
        "prerequisites": parents,
    }


@pytest.mark.parametrize(
    "concepts",
    [
        [concept("aa", ["bb"]), concept("bb", ["aa"])],
        [concept("aa", ["unknown"]), concept("bb", [])],
        [concept("aa", []), concept("aa", [])],
    ],
)
def test_invalid_knowledge_graphs_are_rejected(concepts):
    with pytest.raises(ValidationError):
        KnowledgeMap(subject="A subject", concepts=concepts)


def test_map_is_namespaced_topological_and_persisted(db):
    data = KnowledgeMap(subject="Ecology", concepts=[concept("advanced", ["basics"]), concept("basics", [])])
    subject = Subject(id="ecology", name="Ecology")
    db.add(subject)
    db.flush()
    ids = store_map(db, data, subject)
    db.commit()
    assert ids == ["ecology_basics", "ecology_advanced"]


def test_store_is_deduplicated_and_unknown_concepts_rejected(db):
    card = CardData.model_validate(valid_card())
    first = store_card(db, card)
    assert store_card(db, card).id == first.id
    with pytest.raises(ValueError):
        store_card(db, CardData.model_validate({**valid_card(), "concept_id": "nonexistent"}))


def test_ai_semantic_validation_rejects_out_of_scope_concepts_before_caching(db):
    result = CardBatch(cards=[CardData.model_validate({**valid_card(), "concept_id": "unrequested"})])
    responses = FakeResponses(result)
    ai = AIService(db, client=SimpleNamespace(responses=responses))
    with pytest.raises(AIUnavailable):
        ai.generateLessons([{"id": "complexity"}], 1, [])
    audit = db.scalar(select(AIGeneration))
    assert audit.status == "error" and audit.result is None


class FakeResponses:
    def __init__(self, result, fail=False):
        self.calls = 0
        self.result = result
        self.fail = fail
        self.last_input = None

    def parse(self, **kwargs):
        self.calls += 1
        self.last_input = kwargs
        if self.fail:
            raise TimeoutError("Request timed out")
        return SimpleNamespace(
            output_parsed=self.result, usage=SimpleNamespace(input_tokens=120, output_tokens=80)
        )


def test_structured_ai_mode_validates_caches_and_tracks_usage(db, monkeypatch):
    monkeypatch.setattr(config, "ai_daily_budget_usd", 0.25)
    responses = FakeResponses(
        TutorResponse(
            answer="Binary search halves the remaining interval each step.",
            follow_up="How many halvings reduce 32 to 1?",
        )
    )
    ai = AIService(db, client=SimpleNamespace(responses=responses))
    first = ai.structured("tutor", {"question": "Why logarithmic?"}, TutorResponse)
    assert ai.structured("tutor", {"question": "Why logarithmic?"}, TutorResponse) == first
    assert responses.calls == 1
    row = db.scalar(select(AIGeneration))
    assert row.status == "success" and row.input_tokens == 120 and row.output_tokens == 80
    assert row.estimated_cost > 0
    assert responses.last_input["store"] is False
    assert responses.last_input["model"] == config.openai_model


def test_budget_blocks_call_before_spending(db, monkeypatch):
    monkeypatch.setattr(config, "ai_daily_budget_usd", 0)
    responses = FakeResponses(None)
    with pytest.raises(AIUnavailable, match="budget"):
        AIService(db, client=SimpleNamespace(responses=responses)).structured(
            "tutor", {"q": "why"}, TutorResponse
        )
    assert responses.calls == 0


@pytest.mark.parametrize("fail", [True, False])
def test_failed_or_refused_response_preserves_audit_without_storing_content(db, fail):
    responses = FakeResponses(None, fail=fail)
    ai = AIService(db, client=SimpleNamespace(responses=responses))
    with pytest.raises(AIUnavailable):
        ai.structured("lessons", {"concept": "complexity"}, CardBatch)
    audit = db.scalar(select(AIGeneration))
    assert audit.status == "error" and audit.result is None
    assert audit.error in ("TimeoutError", "ValueError")
    assert db.scalar(select(func.count(LearningCard.id))) == 100
    with pytest.raises(AIUnavailable, match="recently failed"):
        ai.structured("lessons", {"concept": "complexity"}, CardBatch)
    assert responses.calls == 1


def test_buffer_generates_without_swipe_and_honors_high_water(factory, monkeypatch):
    from app.services import buffer
    from app.services.settings import set_setting

    monkeypatch.setattr(buffer, "SessionLocal", factory)
    monkeypatch.setattr(config, "openai_api_key", "test-key-never-sent")
    monkeypatch.setattr(config, "content_buffer_target", 35)
    generated = []

    def lessons(self, concepts, count, titles, source):
        generated.append(concepts)
        return CardBatch(cards=[CardData.model_validate({**valid_card(), "concept_id": concepts[0]["id"]})])

    monkeypatch.setattr(AIService, "generateLessons", lessons)
    with factory() as db:
        set_setting(db, "onboarded", True)
        db.commit()
    buffer.replenish_once()
    buffer.replenish_once()
    assert len(generated) == 1
    with factory() as db:
        assert db.scalar(select(func.count(LearningCard.id)).where(LearningCard.source == "ai")) == 1
