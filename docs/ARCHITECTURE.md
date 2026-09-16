# Architecture and boundaries

Lilt is a local, single-user application. No accounts, social graph, uploads to a public service, video generation, or tracking providers are included.

## Runtime

```text
Browser (React + CSS scroll snap)
    │ same-origin /api requests
Next.js server (UI + HTTP proxy)
    │ private server-to-server request
FastAPI
    ├── recommendation scoring → saved recommendation decisions
    ├── interaction ingestion → mastery → spaced review schedule
    ├── paths / knowledge / progress → the same mastery records
    ├── AI service → OpenAI Responses API (optional)
    └── SQLAlchemy → SQLite file or PostgreSQL

Background worker (one process, every 30 seconds)
    ├── selected subjects without maps → validated knowledge map
    └── low eligible content buffer → validated cached card batch
```

The frontend contains presentation, input handling, chart arithmetic, and navigation. Learning rules live in Python services. All routes use the same SQLAlchemy models. `CardData`, `KnowledgeMap`, and `TutorResponse` are the input boundaries for generated content.

## Stored state

| Table | Purpose |
| --- | --- |
| `subjects`, `topics`, `concepts` | Selected interests and a curriculum hierarchy |
| `concept_dependencies` | Edges from a concept to prerequisite concepts |
| `learning_cards` | Validated renderer data, source, fingerprint, and creation time |
| `questions` | Quiz choices, correct index, and answer explanation; correct indexes are withheld by the feed API |
| `user_concept_mastery` | One user's mastery, confidence, interest, exposures, retrieval record, and next review |
| `recommendations` | One presentation ID per delivered card, score components, weights, seed, and selection reason |
| `interactions` | Shown, dwell, answer, known, deeper, tutor, skipped, revisited, and saved events |
| `reviews` | Answer history with before/after mastery and resulting schedule |
| `saved_cards` | Durable bookmarks |
| `learning_paths` | Ordered references to the same concepts used by the feed |
| `ai_generations` | Cached results, status, token counts, costs/reservations, and sanitized errors |
| `imported_documents` | Original text, fingerprint, subject, and processing state |
| `settings` | Level, onboarding, weights, appearance, learning intention, and AI toggle |

Foreign keys and uniqueness constraints are enforced in both databases. SQLite uses WAL and a 30-second busy timeout. A short process-level write lock serializes writes for this one-user application. Do not run multiple Uvicorn workers; cost reservations and content generation also assume one process. The default server binds to loopback.

## Content format and rendering

Six card kinds are supported: microlesson, quiz, flashcard, visualization, example, challenge. The API returns data, never model-generated executable code or HTML. React escapes prose and code snippets. KaTeX handles equations with `trust=false`, limited expansion, and bounded size. Visuals are an enum of locally implemented renderers:

- `array_elimination`: sorted, finite array; each step is calculated by the renderer.
- `vector`: exactly two finite coordinates; adjustable components.
- `growth`: input-size slider and linear/logarithmic curves.
- `steps`: bounded labels with one-step reveal.

Generated responses are checked for types, lengths, bounds, valid answer indexes, unique answer choices, known concept IDs, existing prerequisite IDs, and cycles. The entire batch's concept scope is checked before any card is inserted. Fingerprints deduplicate exact content. Schema validation cannot guarantee factual correctness; handwritten seed content provides a dependable offline base, and generated content is identified by its source in API records.

## Frontend flow

`useFeed` holds a small prefetched queue (four cards). Swiping never invokes a model. After a quiz, self-report, or tutor/deeper action, it keeps the current and previously shown cards and replaces the unshown tail with newly scored cards. Request cancellation and generation counters discard stale fetch results. At more than 60 buffered/history cards, it trims 30 old cards once at least 40 have been passed and restores the current scroll position; backwards navigation retains at least ten earlier cards.

Each presentation has a unique identifier. `(presentation_id, kind)` is unique in the database, so retries and React development effect replay cannot grade the same answer twice. Quiz retries return the original answer outcome. Dwell is counted only while the document is visible, capped at ten minutes per presentation, and sent on leaving/closing using `keepalive`. Revisit is recorded separately; the MVP does not add a second dwell interval for revisits of the same presentation. Offscreen prefetched cards do not count as seen.

The persistent layout owns the app shell so opening a saved card survives navigation. All progress and bookmarks survive closing the browser. The current feed scroll position and tutor transcript are session-local; opening the app again requests a fresh personalized feed.

## Low-cost AI workflow

`AIService` centralizes model calls. The model comes from `OPENAI_MODEL`; no frontend key exists. Methods are `generateKnowledgeMap`, `generateLessons`, `generateQuiz`, `explainConcept`, `generateExample`, `generateChallenge`, and `expandConcept`. Go deeper is implemented through contextual tutoring; it does not silently append a new curriculum branch.

The Responses API uses `responses.parse(..., text_format=PydanticModel, store=False)`. An exact prompt/schema-version/model fingerprint caches valid results. Tutor context includes only the current card, current concept, prerequisite mastery, up to five recent answer records filtered for mistakes, and up to six conversation messages. It never sends the full learning database. Each call has a bounded output and a timeout; SDK retries are disabled so one budget reservation corresponds to one attempt.

The buffer counts **unseen, prerequisite-eligible** selected content. Below the low threshold (20), a refill cycle produces six cards per tick until the target (100) is met. It generates an initial AI batch even when seeds are already available. Missing maps/cards for selected custom subjects take precedence. Failed calls have a five-minute exact-request cooldown; successful content stays usable if AI fails. This deliberately avoids Celery/Redis for one user.

Budgeting happens before calls under one generation lock. UTF-8 byte counts plus schema/instruction allowance conservatively estimate input tokens; maximum output tokens reserve output cost. A successful response replaces the reservation with reported usage × configured prices. Refusals/incomplete responses retain reported usage when known. Network errors retain conservative reservations when usage is unknown. All reservations count toward the configured UTC daily ceiling. This is a local estimate, not provider billing enforcement; rates must be updated when changing models and a provider project budget is still useful.

## Import behavior

Text and Markdown only, 50–40,000 characters. With AI, an imported subject is processed into a validated graph, then buffered lessons and quizzes; the original text is used as grounding. Without AI, up to 24 bounded passages become reading and recall cards, with original excerpts and no fabricated quiz or prerequisite inference. The complete original text remains stored even if the local excerpt limit is reached. Local imports are not automatically reinterpreted after adding a key; adding the key enables new AI content for the existing concepts, while new imports use AI mapping. Duplicate text returns the existing record.

## Persistence and future changes

The initial schema is created with SQLAlchemy `create_all` on startup and seeded only for an empty database. This is suitable for the delivered schema, **not a schema migration framework**. Add Alembic before changing an installed database's columns/tables. Switching `DATABASE_URL` to PostgreSQL creates a separate database; it does not copy old progress. Keep the original file and use a deliberate migration if retaining it in PostgreSQL is needed.

All persisted timestamps are UTC; JSON dates have a `Z` suffix. Streak/day grouping uses `LEARNING_TIMEZONE`, supplied through Python's zoneinfo and tzdata. No arbitrary file paths are accepted from import requests. CORS and an Origin check constrain browser writes, but this is not authentication. Keep it on loopback; remote deployment would need authentication and a distributed job/budget lock.

## Main endpoints

`GET /api/health`, `GET/PATCH /api/settings`, `POST /api/onboarding`, `GET /api/feed`, `POST /api/interactions`, `GET /api/knowledge`, `GET /api/progress`, `GET /api/saved`, `PUT /api/cards/{id}/saved`, `POST /api/cards/{id}/open`, `POST /api/tutor`, `GET /api/usage`, `GET/POST /api/imports`.

Interactive schemas and request examples are available at `http://127.0.0.1:8000/docs` while the backend runs. Responses are marked `Cache-Control: no-store`; model content caching occurs in the database, not in browser HTTP caches.
