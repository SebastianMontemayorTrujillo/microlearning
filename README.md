# Lilt — a little wiser, every day

A complete local MVP for one person's learning: a vertical feed, interactive lessons, adaptive recommendations, a personal knowledge map, and spaced retrieval. Built with **Next.js + React + TypeScript + Tailwind**, **FastAPI**, and **SQLAlchemy**. SQLite works immediately; PostgreSQL is optional.

**No API key is required to start.** The app includes **100 handwritten cards**, **20 concepts**, **6 topics**, and **4 learning paths** in Computer Science and Mathematics. No fake progress or user history is seeded.

## What works

- Native vertical scroll/snap feed, touch swiping, keyboard ↑/↓, and previous-card navigation.
- Six card formats: lessons, quizzes, flashcards, visualizations, examples, challenges.
- Interactive binary search, vector components, growth charts, step reveals, and KaTeX equations.
- Backend grading, durable bookmarks, exposure/dwell tracking, and idempotent answers.
- Mastery based on evidence and forgetting, prerequisite gates, adaptive review intervals.
- Scored recommendations with persisted reasons and configurable weights. Answers re-rank upcoming cards.
- Onboarding with arbitrary subjects and an initial level; AI creates maps for new subjects when enabled.
- Learning paths and a knowledge map using the same mastery as the feed.
- A progress dashboard with topic/subject mastery, due concepts, weak concepts, streak, and visible learning time.
- Contextual OpenAI tutoring and validated, cached AI lessons; explicit local study help without a key.
- A low-water content buffer, per-day local cost ceiling, token estimates, and usage history.
- Text/Markdown import. Without AI, it creates honest excerpt cards; with AI, it builds a map and lessons.
- Dark/light themes, a mobile layout, error states, and an accessible tutor dialog.

There is no social network, authentication flow, generated video, paid analytics, or external recommendation service.

## Windows PowerShell: exact setup

Use **two PowerShell windows**: one for the backend and one for the frontend. Commands below assume the downloaded/extracted project is at `C:\Projects\soniapp`. Replace that path with your actual folder when needed. You should see `frontend`, `backend`, and this README inside it.

### 1. Required software

Install **Python 3.12**, **Node.js 22 or newer**, and optionally Git. Docker is **not** required for the standard SQLite setup.

If Windows Package Manager (`winget`) is available:

```powershell
winget install --exact --id Python.Python.3.12
winget install --exact --id OpenJS.NodeJS.LTS
```

Alternatively, use the installers from [python.org](https://www.python.org/downloads/windows/) and [nodejs.org](https://nodejs.org/en/download). Select **Add Python to PATH** if offered. Keep Node's npm component enabled.

Close and reopen PowerShell after installation, then verify:

```powershell
py -3.12 --version
node --version
npm.cmd --version
```

Use `npm.cmd` on Windows if execution policy blocks `npm.ps1`.

### 2. Open the project and create a Python environment

In **PowerShell window 1**:

```powershell
Set-Location C:\Projects\soniapp
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r backend\requirements.txt
```

The `.venv` directory holds this project's Python dependencies separately from your other programs. Commands use its interpreter explicitly, so activating it is not necessary.

Optional activation, if you prefer typing `python` instead of the full interpreter path:

```powershell
.\.venv\Scripts\Activate.ps1
```

If activation is blocked by execution policy, continue with the explicit interpreter commands above; no system policy change is necessary.

### 3. Create `.env`

Still in the project root:

```powershell
if (-not (Test-Path .env)) { Copy-Item .env.example .env }
notepad .env
```

For free local/demo mode, leave these entries empty:

```dotenv
OPENAI_API_KEY=
DATABASE_URL=
```

Do not rename `.env` to `.env.txt`. Notepad's Save As dialog should use **All files** if necessary. The backend reads `.env` from the repository root regardless of where the command is started.

### 4. Database setup

**SQLite is the default and needs no installation.** On its first start, the backend creates tables and the seeded curriculum in:

```text
backend/microlearn.db
```

That file stores your progress, bookmarks, preferences, generated lessons, and imported text. Closing your browser or restarting either server does not erase it. SQLite may also create `microlearn.db-wal` and `microlearn.db-shm` while running.

Keep `DATABASE_URL=` empty to use SQLite. See the PostgreSQL section below only if you want a separate database server.

### 5. Start the backend

In **PowerShell window 1**, from the repository root:

```powershell
.\.venv\Scripts\python.exe -m uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8000 --reload
```

Leave this window open. You should see `Application startup complete` and a URL using port 8000. The `--reload` option restarts Python when source code changes. Use one worker only.

In a spare PowerShell window you can check it:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/api/health
```

Expected: `status: ok`, `mode: demo` (or `ai` with a configured, enabled key). Interactive API documentation is at [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs).

### 6. Install and start the frontend

Open **PowerShell window 2**:

```powershell
Set-Location C:\Projects\soniapp\frontend
npm.cmd ci
npm.cmd run dev
```

`npm ci` installs the versions in `package-lock.json`. Leave this window open too.

### 7. Open the application

Open **[http://127.0.0.1:3000](http://127.0.0.1:3000)** or [http://localhost:3000](http://localhost:3000).

Choose Computer Science and/or Mathematics, pick your starting level, and start learning. On desktop, scroll or press ↓ to advance and ↑ to return. On mobile, swipe vertically. Longer cards can scroll internally; continue swiping at the bottom or use the small next/previous arrows.

Answer a question under **Practice & review** after viewing a lesson. This immediately updates mastery and the next review date. Go to **Learn → Knowledge map** to see prerequisites unlock. Bookmark a card and find it in **Saved**. Open **Progress** to see the same learning state summarized.

The first due review is normally tomorrow. Incorrect answers schedule a retry in ten minutes. You can practice encountered concepts immediately; the UI distinguishes practice from a due review. The seed does not pretend that you learned things yesterday.

### 8. Stop and restart later

Press **Ctrl+C** in both running server windows. Next time, only start the backend and frontend again; dependency installation and onboarding are not repeated.

Backend, from the project root:

```powershell
.\.venv\Scripts\python.exe -m uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8000 --reload
```

Frontend, from its folder:

```powershell
npm.cmd run dev
```

## Enable OpenAI

The API key belongs **only in the root `.env` file**, never in `frontend`, React code, or a `NEXT_PUBLIC_*` variable.

```dotenv
OPENAI_API_KEY=your-api-key-here
OPENAI_MODEL=gpt-4.1-mini
AI_DAILY_BUDGET_USD=0.25
AI_INPUT_USD_PER_MILLION=0.40
AI_OUTPUT_USD_PER_MILLION=1.60
CONTENT_BUFFER_LOW=20
CONTENT_BUFFER_TARGET=100
AI_BATCH_SIZE=6
```

Obtain a key from your [OpenAI API account](https://platform.openai.com/api-keys). API access and billing are separate from the local app. Restart the backend after changing `.env`; source reload does not reliably reload environment files. Leave **Settings → AI & usage → AI enabled** switched on.

After onboarding, the worker checks the buffer every 30 seconds. It starts with an initial AI batch, builds missing maps for selected subjects, and generates additional batches as needed. New cards are validated, stored, and become recommendation candidates. The API is **not called on every swipe**. If generation is slow or unavailable, the stored feed continues working.

Routine generation and the tutor use the one configured model. The default is a small model that supports structured outputs. If you change the model, choose one with Responses API structured-output support and update the cost rates. The implementation follows the official [Structured Outputs guide](https://developers.openai.com/api/docs/guides/structured-outputs) and the [GPT-4.1 mini model documentation](https://developers.openai.com/api/docs/models/gpt-4.1-mini), checked while building this app.

The app validates response shape, lengths, correct-answer indexes, allowed renderers, and graph prerequisites. This does not prove factual accuracy. Tutor responses are plain text; “explain visually” can use textual diagrams, while interactive card visuals use the four supplied renderers. Open-ended tutoring, new custom-subject maps, and new AI explanations require the key.

**Settings → AI & usage** reports token usage, cached results, generated card counts, estimated costs, and sanitized errors. Prices are environment-configured estimates. The local daily budget uses UTC and conservatively reserves cost before requests; it is not an OpenAI billing API. Set a project budget in your API account as well. Network failures may retain a conservative reservation because actual usage is unknown.

## Learn from your own notes

Go to **Learn → Teach me this**. Choose a `.txt`, `.md`, or `.markdown` file, or paste 50–40,000 characters and supply a title.

- **Without a key:** up to 24 bounded source passages become reading/recall cards and a path in source order. The full original text remains stored. No generated quiz or inferred prerequisite is claimed.
- **With AI:** the source is sent to OpenAI to create a prerequisite map and structured lessons/quizzes. Processing is asynchronous. Use **Refresh processing status** to check progress; a map can appear before its lesson buffer finishes. Custom subjects also appear after background processing.
- Reimporting identical text returns the existing document.
- PDF extraction is deliberately not included in this MVP.

Local imports already mapped as excerpts keep their original map after a key is added; new AI cards can be generated for those concepts. New imports made with AI enabled get AI-created maps.

## Tests and checks

All tests use temporary databases. They do not change your real learning history or make paid model calls.

Backend algorithms, persistence/API integration, AI validation, caching, budgets, failure handling, and buffer tests — from the repository root:

```powershell
Set-Location C:\Projects\soniapp
Push-Location backend
..\.venv\Scripts\python.exe -m pytest -q
..\.venv\Scripts\python.exe -m mypy app
..\.venv\Scripts\python.exe -m ruff check app tests
Pop-Location
```

Frontend type check and production build:

```powershell
Set-Location C:\Projects\soniapp\frontend
npm.cmd run typecheck
npm.cmd run build
```

End-to-end desktop/mobile tests (install Chromium once):

```powershell
Set-Location C:\Projects\soniapp\frontend
npx.cmd playwright install chromium
npm.cmd run test:e2e
```

These tests start separate servers on ports **8001** and **3001**, create an isolated temporary SQLite database, and force demo mode. Keep those ports free. Your regular servers on 8000/3000 may stay running. The test configuration uses the `.venv` in the root; if you named yours differently, change the interpreter path in `frontend/playwright.config.ts`.

Failure screenshots go under `frontend/test-results`. For a full diagnostic run with trace recording and desktop/mobile screenshots (uses more memory):

```powershell
$env:PW_TRACE = "1"
$env:CAPTURE_SCREENSHOTS = "1"
npm.cmd run test:e2e
Remove-Item Env:PW_TRACE
Remove-Item Env:CAPTURE_SCREENSHOTS
```

To inspect a reported trace:

```powershell
npx.cmd playwright show-trace "test-results\the-reported-test-folder\trace.zip"
```

For a production-style local frontend after a successful build:

```powershell
npm.cmd run start
```

Stop `npm run dev` first because both use port 3000. Keep the backend running. Normal builds contain no API key.

## macOS / Linux quick start

From the repository root:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r backend/requirements.txt
cp -n .env.example .env
.venv/bin/python -m uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8000 --reload
```

In a second terminal:

```bash
cd frontend
npm ci
npm run dev
```

Use `../.venv/bin/python -m pytest -q` from `backend` for backend tests. The implementation was verified on Linux with Python 3.14 and Node 22; the Windows instructions target Python 3.12. Windows execution itself was not available in the build environment.

## Optional Docker

Install Docker Desktop, start it, and copy `.env.example` to `.env` as above. With `DATABASE_URL=` empty, this launches the whole app using a persistent SQLite volume:

```powershell
Set-Location C:\Projects\soniapp
docker compose up --build
```

Open http://localhost:3000. Stop with Ctrl+C, then:

```powershell
docker compose down
```

The named volume retains your database. **Do not add `--volumes` / `-v` unless you intend to delete the database.** The Docker database is separate from the local Python process's `backend/microlearn.db`.

Docker was not installed in the implementation environment, so this configuration is supplied but was not executed there.

## Optional PostgreSQL

SQLAlchemy uses PostgreSQL-compatible types and the `psycopg` driver. A fresh database creates the same tables and seeds at startup. You can use an existing PostgreSQL server, or start only the included database container:

```powershell
Set-Location C:\Projects\soniapp
docker compose --profile postgres up -d db
docker compose --profile postgres ps
```

Wait for the database to be healthy. For a backend running directly in your Windows virtual environment, set in `.env`:

```dotenv
DATABASE_URL=postgresql+psycopg://lilt:lilt_local_only@127.0.0.1:5432/lilt
```

Restart the backend. The included credentials are for a loopback-only local development database. For a backend also running in Docker, use host **db**, not **127.0.0.1**:

```dotenv
DATABASE_URL=postgresql+psycopg://lilt:lilt_local_only@db:5432/lilt
```

Start the `db` service first as above, then `docker compose --profile postgres up --build`. The frontend/backend ports are bound to your local machine.

**Switching database URLs does not migrate existing progress.** Your SQLite file stays intact. Return to an empty `DATABASE_URL` to use it again. A data-preserving SQLite-to-PostgreSQL transfer and future schema upgrades require a deliberate migration; no automatic destructive conversion exists. PostgreSQL runtime was not available during implementation, so database integration tests ran against SQLite.

## Back up your progress

For the standard SQLite setup, stop the backend with Ctrl+C so its WAL is checkpointed, then run from the repository root:

```powershell
New-Item -ItemType Directory -Force backups | Out-Null
$BackupFile = "backups\microlearn-$(Get-Date -Format 'yyyyMMdd-HHmmss').db"
Copy-Item backend\microlearn.db $BackupFile
```

Keep backups private: they contain your learning history and imported text. Back up before changing database schema or moving installations. Copying only the main database file while a WAL writer is running can miss recent transactions.

## Troubleshooting

| Problem | What to do |
| --- | --- |
| `py` or `node` not found | Reopen PowerShell after installation. Verify the software was installed and added to PATH. |
| `No suitable Python runtime found` | Install Python 3.12 with the command above, or replace `-3.12` with your installed supported version. |
| `npm.ps1 cannot be loaded` | Use `npm.cmd` and `npx.cmd` as shown. |
| `Activate.ps1` is blocked | Skip activation and use `.\.venv\Scripts\python.exe` explicitly. |
| `No module named app` | Start from the root with `--app-dir backend`, or change to `backend` and omit that option. |
| `No module named fastapi` | Install requirements using the same `.venv` interpreter used to launch Uvicorn. |
| `Cannot reach the learning engine`, 502, or 500 | Ensure backend window is still running; visit `/api/health` directly on port 8000 and read the backend error. Check `.env` database settings. |
| Port 3000 or 8000 already in use | Stop the earlier process with Ctrl+C. For a different backend port, set `BACKEND_URL` for the frontend process and restart it; for a different frontend port, update `FRONTEND_ORIGIN` in root `.env` and restart the backend. |
| Running the frontend on another backend | In frontend PowerShell, use `$env:BACKEND_URL = "http://127.0.0.1:8002"` before starting/building Next.js. This is a server setting, not a secret. |
| Custom topic has no cards in local mode | Select Computer Science or Mathematics, import your own text, or enable an API key. The app does not invent offline facts for arbitrary subjects. |
| I added a key but still see local mode | Restart the backend, refresh the page, confirm `.env` is in the root and not named `.env.txt`, and check the AI toggle. |
| AI error or no new content | Inspect Settings → AI & usage and backend logs. Check the model, key, API account balance, and local daily budget. Identical failed requests cool down for five minutes. No secret headers are logged. |
| No AI card on the very next swipe | Buffer jobs run every 30 seconds; missing maps are generated before cards. New content is mixed by the recommender, so cached lessons can still rank first. |
| Budget reached with few completed requests | Failed/unfinished calls conservatively reserve possible usage. Review the request history; the local daily limit resets at midnight UTC. |
| No reviews due yet | The fresh seed has no pretend history. Read or answer a lesson to schedule one, or use Practice & review for immediate practice. |
| Progress looks lower later | Estimated retention decays with time. Review strengthens it. Raw stored mastery and effective mastery are both available in the API. |
| Progress disappeared | Check that you did not change `DATABASE_URL`, delete/move `backend/microlearn.db`, or switch between Docker and the local Python backend. These use separate databases. |
| SQLite is locked | Use one backend process, close tools holding write transactions, then restart. Do not run multiple Uvicorn workers. |
| Browser tests say Chromium is missing | Run `npx.cmd playwright install chromium`. On Linux, missing system libraries may require `npx playwright install-deps chromium`. |
| Test ports already in use | Free 3001 and 8001; tests intentionally do not reuse a potentially real database server. |
| `next dev` says a lock is held | Stop the earlier development server. Tests use a separate `.next-e2e` output directory. |

## Repository map

```text
soniapp/
├── frontend/
│   ├── app/                 Next.js routes, layout, responsive styling
│   ├── components/          Feed, renderers, tutor, paths, dashboards
│   ├── hooks/               Feed buffering, exposure lifecycle, API resources
│   ├── lib/                 Same-origin API client
│   ├── types/               Strict TypeScript contracts
│   └── tests/               Desktop + mobile Playwright integration tests
├── backend/
│   ├── app/
│   │   ├── api/             Validated HTTP endpoints
│   │   ├── models/          SQLAlchemy persistence
│   │   ├── schemas/         Pydantic AI and request schemas
│   │   ├── services/        Mastery, scheduling, scoring, AI, content buffer
│   │   ├── seed.py          Handwritten CS + math curriculum
│   │   └── main.py          FastAPI startup and local browser-write guard
│   └── tests/               Algorithms, API, AI contract and persistence tests
├── docs/
│   ├── ALGORITHMS.md        Formulas, weights, scheduling, and limitations
│   └── ARCHITECTURE.md      Boundaries, schema, buffering, imports, API
├── .env.example
├── docker-compose.yml
└── README.md
```

Read [the recommendation and mastery formulas](docs/ALGORITHMS.md) and [architecture notes](docs/ARCHITECTURE.md) before tuning behavior. All seed records start with zero actual learning evidence. The app is intentionally loopback-only and has no authentication: do not expose it publicly without adding access control. AI output validation and budget locks are designed for one running backend process.
