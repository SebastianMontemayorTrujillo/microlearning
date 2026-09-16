from sqlalchemy.orm import Session

from app.models import Setting

DEFAULT_WEIGHTS = {
    "learning_value": 1.2,
    "review_urgency": 2.4,
    "difficulty_match": 1.0,
    "interest": 0.7,
    "prerequisite_relevance": 0.8,
    "novelty": 0.8,
    "variety": 0.7,
    "repetition_penalty": 2.0,
    "exploration": 0.2,
}
DEFAULT_SETTINGS = {
    "onboarded": False,
    "level": "beginner",
    "theme": "dark",
    "daily_minutes": 10,
    "ai_enabled": True,
    "weights": DEFAULT_WEIGHTS,
}


def get_setting(db: Session, key: str):
    row = db.get(Setting, key)
    return row.value if row else DEFAULT_SETTINGS.get(key)


def set_setting(db: Session, key: str, value):
    row = db.get(Setting, key)
    if row:
        row.value = value
    else:
        db.add(Setting(key=key, value=value))
