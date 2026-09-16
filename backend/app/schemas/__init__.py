from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class QuizData(StrictModel):
    question: str = Field(min_length=5, max_length=600)
    answers: list[str] = Field(min_length=2, max_length=4)
    correct: int = Field(ge=0, le=3)
    explanation: str = Field(min_length=10, max_length=2000)

    @model_validator(mode="after")
    def valid_answer(self):
        if self.correct >= len(self.answers) or len(set(self.answers)) != len(self.answers):
            raise ValueError("Answer index or choices are invalid")
        if any(not a.strip() or len(a) > 400 for a in self.answers):
            raise ValueError("Each answer must contain 1–400 characters")
        return self


class VisualData(StrictModel):
    type: Literal["array_elimination", "vector", "growth", "steps"]
    values: list[float] = Field(max_length=32)
    labels: list[str] = Field(max_length=10)
    caption: str = Field(max_length=500)

    @model_validator(mode="after")
    def valid_visual(self):
        import math

        if any(not math.isfinite(v) or abs(v) > 10000 for v in self.values):
            raise ValueError("Visualization values must be finite and bounded")
        if self.type == "vector" and len(self.values) != 2:
            raise ValueError("Vectors require two coordinates")
        if self.type == "array_elimination" and (len(self.values) < 2 or self.values != sorted(self.values)):
            raise ValueError("Binary search needs a sorted array")
        if self.type == "steps" and not self.labels:
            raise ValueError("Step visualization needs labels")
        return self


class CardData(StrictModel):
    concept_id: str = Field(min_length=1, max_length=100)
    type: Literal["micro_lesson", "quiz", "flashcard", "visualization", "challenge", "example"]
    title: str = Field(min_length=5, max_length=180)
    hook: str = Field(min_length=5, max_length=400)
    explanation: str = Field(min_length=20, max_length=3000)
    takeaway: str = Field(min_length=5, max_length=400)
    difficulty: float = Field(ge=0, le=1)
    estimated_seconds: int = Field(ge=10, le=180)
    steps: list[str] = Field(max_length=6)
    equation: str | None
    code: str | None
    visualization: VisualData | None
    quiz: QuizData | None

    @model_validator(mode="after")
    def consistent_type(self):
        if self.type in ("quiz", "challenge") and self.quiz is None:
            raise ValueError("Retrieval cards require a quiz")
        if self.type == "visualization" and self.visualization is None:
            raise ValueError("Visualization cards need a visual")
        if any(len(s) > 700 for s in self.steps):
            raise ValueError("Step is too long")
        if self.equation and len(self.equation) > 600:
            raise ValueError("Equation is too long")
        if self.code and len(self.code) > 3000:
            raise ValueError("Code is too long")
        return self


class CardBatch(StrictModel):
    cards: list[CardData] = Field(min_length=1, max_length=12)


class MapConcept(StrictModel):
    id: str = Field(pattern=r"^[a-z][a-z0-9_]{1,60}$")
    name: str = Field(min_length=2, max_length=150)
    topic: str = Field(min_length=2, max_length=100)
    summary: str = Field(min_length=15, max_length=1000)
    difficulty: float = Field(ge=0, le=1)
    prerequisites: list[str] = Field(max_length=6)


class KnowledgeMap(StrictModel):
    subject: str = Field(min_length=2, max_length=100)
    concepts: list[MapConcept] = Field(min_length=2, max_length=16)

    @model_validator(mode="after")
    def valid_graph(self):
        graph = {c.id: c.prerequisites for c in self.concepts}
        if len(graph) != len(self.concepts):
            raise ValueError("Concept IDs must be unique")
        visited: set[str] = set()
        visiting: set[str] = set()

        def visit(node: str):
            if node not in graph:
                raise ValueError("Unknown prerequisite")
            if node in visiting:
                raise ValueError("Cyclic prerequisites")
            if node in visited:
                return
            visiting.add(node)
            for parent in graph[node]:
                visit(parent)
            visiting.remove(node)
            visited.add(node)

        for node in graph:
            visit(node)
        return self


class TutorResponse(StrictModel):
    answer: str = Field(min_length=10, max_length=5000)
    follow_up: str = Field(min_length=5, max_length=300)


class OnboardingInput(StrictModel):
    subjects: list[str] = Field(min_length=1, max_length=10)
    level: Literal["beginner", "intermediate", "advanced"] = "beginner"

    @model_validator(mode="after")
    def clean_subjects(self):
        self.subjects = list(dict.fromkeys(s.strip() for s in self.subjects if s.strip()))
        if not self.subjects or any(len(s) > 100 or len(s) < 2 for s in self.subjects):
            raise ValueError("Subject names must contain 2–100 characters")
        return self


class EventInput(StrictModel):
    presentation_id: str = Field(max_length=100)
    kind: Literal["shown", "dwell", "answer", "known", "deeper", "tutor", "skipped", "revisited", "saved"]
    answer: int | None = Field(default=None, ge=0, le=3)
    seconds: float = Field(default=0, ge=0, le=600)


class TutorInput(StrictModel):
    card_id: str = Field(max_length=100)
    message: str = Field(min_length=1, max_length=1000)
    history: list[dict[Literal["role", "content"], str]] = Field(default_factory=list, max_length=6)

    @model_validator(mode="after")
    def safe_history(self):
        for message in self.history:
            if (
                set(message) != {"role", "content"}
                or message["role"] not in ("user", "assistant")
                or len(message["content"]) > 5000
            ):
                raise ValueError("Invalid conversation history")
        return self


class ImportInput(StrictModel):
    title: str = Field(min_length=2, max_length=150)
    text: str = Field(min_length=50, max_length=40000)


class PreferencesInput(StrictModel):
    theme: Literal["dark", "light"] | None = None
    daily_minutes: int | None = Field(default=None, ge=3, le=120)
    weights: dict[str, float] | None = None
    ai_enabled: bool | None = None
