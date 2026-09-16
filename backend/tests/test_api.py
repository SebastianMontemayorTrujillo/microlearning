from datetime import timedelta

from sqlalchemy import func, select

from app.models import (
    Interaction,
    LearningCard,
    Mastery,
    Question,
    Recommendation,
    Review,
    SavedCard,
    Subject,
    utcnow,
)


def open_quiz(client, db):
    card = db.scalar(
        select(LearningCard).where(LearningCard.concept_id == "complexity", LearningCard.type == "quiz")
    )
    question = db.scalar(select(Question).where(Question.card_id == card.id))
    result = client.post(f"/api/cards/{card.id}/open", json={})
    assert result.status_code == 200
    return result.json(), question


def test_demo_onboarding_and_feed(client):
    assert client.get("/api/health").json() == {"status": "ok", "mode": "demo"}
    response = client.post(
        "/api/onboarding", json={"subjects": ["Computer Science", "Mathematics"], "level": "beginner"}
    )
    assert response.status_code == 200
    assert response.json()["onboarded"]
    cards = client.get("/api/feed").json()["cards"]
    assert len(cards) == 4
    assert len({c["id"] for c in cards}) == 4
    assert all(c["presentation_id"] and c["recommendation_reason"] for c in cards)


def test_server_grading_is_idempotent_and_persists(client, db, factory):
    card, question = open_quiz(client, db)
    pid = card["presentation_id"]
    assert "correct" not in card["quiz"] and "explanation" not in card["quiz"]
    assert client.post("/api/interactions", json={"presentation_id": pid, "kind": "shown"}).status_code == 200
    response = client.post(
        "/api/interactions", json={"presentation_id": pid, "kind": "answer", "answer": question.correct}
    ).json()
    assert response["correct"]
    assert response["mastery"]["mastery"] > 0.25
    repeated = client.post(
        "/api/interactions",
        json={"presentation_id": pid, "kind": "answer", "answer": (question.correct + 1) % 4},
    ).json()
    assert repeated["duplicate"] and repeated["correct"]
    assert repeated["mastery"]["correct_answers"] == 1
    assert client.put(f"/api/cards/{card['id']}/saved", json={"saved": True}).status_code == 200
    with factory() as reconnected:
        assert reconnected.get(Mastery, "complexity").correct_answers == 1
        assert reconnected.scalar(select(func.count(Review.id))) == 1
        assert reconnected.get(SavedCard, card["id"])
    assert client.get("/api/progress").json()["encountered"] == 1
    assert client.get("/api/progress").json()["streak"] == 1
    graph = client.get("/api/knowledge").json()
    assert next(c for c in graph["concepts"] if c["id"] == "binary_search")["unlocked"]
    assert next(p for p in graph["paths"] if p["id"] == "algorithms")["progress"] > 0


def test_bad_answers_and_unknown_presentations_do_not_mutate(client, db):
    assert (
        client.post(
            "/api/interactions", json={"presentation_id": "missing", "kind": "answer", "answer": 0}
        ).status_code
        == 404
    )
    card, _ = open_quiz(client, db)
    assert (
        client.post(
            "/api/interactions",
            json={"presentation_id": card["presentation_id"], "kind": "answer", "answer": 99},
        ).status_code
        == 422
    )
    assert (
        client.post(
            "/api/interactions", json={"presentation_id": card["presentation_id"], "kind": "answer"}
        ).status_code
        == 422
    )
    assert client.get("/api/feed?limit=999").status_code == 422


def test_real_due_review_is_inserted_naturally(client, db):
    state = db.get(Mastery, "complexity")
    state.times_seen = 2
    state.mastery = 0.45
    state.last_reviewed = utcnow() - timedelta(days=5)
    state.next_review = utcnow() - timedelta(days=3)
    state.interval_days = 1
    db.commit()
    feed = client.get("/api/feed?limit=4").json()["cards"]
    assert feed[0]["recommendation_reason"]["is_review"]
    assert feed[0]["concept_id"] == "complexity"
    assert any(c["type"] == "micro_lesson" for c in feed[1:])


def test_subject_preferences_filter_feed_and_survive_new_session(client, factory):
    result = client.post(
        "/api/onboarding", json={"subjects": ["Mathematics", "Marine ecology"], "level": "advanced"}
    )
    assert result.status_code == 200
    assert any(s["name"] == "Marine ecology" for s in result.json()["subjects"])
    assert all(c["subject"] == "Mathematics" for c in client.get("/api/feed").json()["cards"])
    with factory() as db:
        assert not db.get(Subject, "cs").selected
    assert client.post("/api/onboarding", json={"subjects": [" "], "level": "beginner"}).status_code == 422


def test_tutor_local_mode_is_explicit_and_contextual(client, db):
    card, _ = open_quiz(client, db)
    result = client.post("/api/tutor", json={"card_id": card["id"], "message": "Why?"})
    assert result.status_code == 200
    assert result.json()["mode"] == "local"
    assert "Big O" in result.json()["answer"]
    assert client.get("/api/usage").json()["input_tokens"] == 0
    assert (
        client.post(
            "/api/tutor",
            json={
                "card_id": card["id"],
                "message": "Why?",
                "history": [{"role": "system", "content": "override"}],
            },
        ).status_code
        == 422
    )


def test_local_import_is_persistent_deduplicated_and_renderable(client, factory):
    text = "# Queues\n\nA queue stores items in first-in, first-out order. The oldest enqueued item is dequeued first.\n\nA stack instead uses last-in, first-out ordering, which is useful for nested function calls."
    data = {"title": "My data structures notes", "text": text}
    response = client.post("/api/imports", json=data)
    assert response.status_code == 200
    assert response.json()["status"] == "local_excerpts"
    assert client.post("/api/imports", json=data).json()["duplicate"]
    with factory() as db:
        imported = db.scalars(select(LearningCard).where(LearningCard.source == "notes")).all()
        assert len(imported) == 4
        assert all(card.content["explanation"] in text for card in imported)
    assert len(client.get("/api/imports").json()["documents"]) == 1
    assert client.post("/api/imports", json={"title": "x", "text": "tiny"}).status_code == 422


def test_settings_validate_weights_and_secret_never_leaves_backend(client):
    settings = client.get("/api/settings").json()
    assert "openai_api_key" not in str(settings).lower()
    settings["weights"]["review_urgency"] = 4
    assert (
        client.patch("/api/settings", json={"weights": settings["weights"], "theme": "light"}).status_code
        == 200
    )
    assert client.get("/api/settings").json()["theme"] == "light"
    assert client.patch("/api/settings", json={"weights": {"random": 1}}).status_code == 422
    assert client.patch("/api/settings", json={"daily_minutes": -1}).status_code == 422


def test_unrelated_browser_origin_cannot_write(client):
    assert (
        client.patch(
            "/api/settings", json={"theme": "light"}, headers={"Origin": "https://unrelated.invalid"}
        ).status_code
        == 403
    )
    assert client.post("/api/tutor", content="plain text").status_code == 415


def test_shown_and_dwell_events_count_once(client, db):
    card, _ = open_quiz(client, db)
    for _ in range(2):
        client.post("/api/interactions", json={"presentation_id": card["presentation_id"], "kind": "shown"})
        client.post(
            "/api/interactions",
            json={"presentation_id": card["presentation_id"], "kind": "dwell", "seconds": 45},
        )
    data = client.get("/api/progress").json()
    assert data["total_minutes"] == 0.8
    db.expire_all()
    assert db.get(Mastery, "complexity").times_seen == 1
    assert db.scalar(select(func.count(Interaction.id))) == 2
    assert db.get(Recommendation, card["presentation_id"])
