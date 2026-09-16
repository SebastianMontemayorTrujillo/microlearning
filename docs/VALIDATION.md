# Verification record

Verified on 2026-09-15 in the implementation environment: Linux, Python 3.14.4, Node 22.23.2, npm 10.9.8, SQLite, Next.js 16.3.5, and Chromium through Playwright. See package lockfiles / pinned requirements for dependency versions.

| Check | Result |
| --- | --- |
| Backend pytest | **39 passed** |
| Python type checking (`mypy app`) | Passed, 19 source files |
| Python lint (`ruff check app tests`) | Passed |
| Next.js production build | Passed |
| TypeScript (`tsc --noEmit`) | Passed |
| Frontend formatting | Passed |
| Browser integration | **4 passed** |
| Real backend process stop/restart | Progress, settings, bookmarks and review dates preserved |
| Demo mode | Seeded curriculum and complete local learning loop exercised without a key |

The browser flows cover onboarding, a visible first lesson, bookmarking, recommendation reasons, contextual local tutoring, quiz submission, prerequisite unlock, saved-card revisits, progress, import, theme persistence, API usage, actual mobile touch scrolling, previous-card navigation, flashcard reveal, tutor failure/retry, and a 65-card feed session with bounded DOM history and preserved scroll position. Desktop/mobile screenshots were captured and visually inspected. Regular tests omit optional screenshot captures and tracing to reduce memory use; failure screenshots remain enabled.

The OpenAI path was tested with mocked responses for schema/semantic validation, response caching, token/cost accounting, refusal/timeout recovery, budget enforcement, and background refill. **No OpenAI credentials were present, so no live model call was made.** Docker, PostgreSQL runtime, native Windows execution, Safari, and Firefox were not available/tested. Their setup or compatibility paths are documented without claiming execution.

The backend suite reports two upstream TestClient deprecation warnings under Python 3.14; they do not affect passing assertions. A browser rerun encountered resource-related startup/screenshot errors while the machine was under memory pressure; running checks sequentially resolved the issue. All final functional assertions and production checks passed.

Tests use isolated temporary databases and empty API keys. The delivered local database retains zero fabricated learning history and starts at onboarding. The development servers were replaced with the final production frontend and backend for the local handoff.
