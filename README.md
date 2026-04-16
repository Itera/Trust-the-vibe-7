# Trust-the-vibe-7

A tiny full-stack chat app that talks to an Azure OpenAI `gpt-4o-mini` deployment.

- **Backend**: FastAPI (Python) — proxies chat requests to Azure OpenAI, keeps the API key off the browser, *and serves the built frontend*.
- **Frontend**: Vite + React + TypeScript — simple chat UI.
- **Tests**: `pytest` on the backend, `vitest` + `@testing-library/react` on the frontend.

## Prerequisites

Install these once:

- Python **3.10+** ([python.org](https://www.python.org/downloads/))
- Node **18+** ([nodejs.org](https://nodejs.org/))

No other system-level tools are needed.

## Quick start (macOS, Linux, Windows)

The same three commands work on every OS.

```bash
# 1. install deps + build the frontend
python scripts/setup.py

# 2. run the app  (UI + API both at http://127.0.0.1:8000)
python scripts/start.py

# 3. run the tests
python scripts/test.py
```

> On Windows, if `python` isn't on your PATH try `py -3` instead (e.g. `py -3 scripts/setup.py`).

Open <http://127.0.0.1:8000> and start chatting. API docs live at <http://127.0.0.1:8000/docs>.

### Script reference

| Script | What it does |
| --- | --- |
| `scripts/setup.py` | Creates `backend/.venv`, installs Python deps, runs `npm install`, builds `frontend/dist`. Idempotent — safe to re-run. |
| `scripts/start.py` | Starts Uvicorn. Accepts `--host`, `--port`, `--reload`. Serves the built SPA at `/` and the API at `/api/*`. |
| `scripts/test.py` | Runs `pytest` + `vitest`. Flags: `--backend-only`, `--frontend-only`. |

### Development mode (hot reload for the frontend)

`start.py` serves the *built* frontend. While iterating on the UI you probably want Vite's dev server instead:

```bash
# terminal 1 — backend with hot reload
python scripts/start.py --reload

# terminal 2 — vite dev server on :5173 (proxies /api → :8000)
cd frontend
npm run dev
```

## Configuration

Backend config lives in `backend/.env` (gitignored). `backend/.env.example` shows the required variable names:

```
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com
AZURE_OPENAI_DEPLOYMENT=gpt-4o-mini
AZURE_OPENAI_API_VERSION=2025-01-01-preview
AZURE_OPENAI_API_KEY=your-key-here
ALLOWED_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
```

## Layout

```
.
├── backend/           FastAPI app + pytest tests
│   ├── app/           main.py, llm.py, config.py, schemas.py
│   └── tests/
├── frontend/          Vite + React + TS app + vitest tests
│   ├── src/           components/Chat.tsx, api.ts, ...
│   └── dist/          built SPA (produced by `npm run build`)
├── scripts/           cross-platform setup/start/test runners
└── README.md
```

## Notes on secrets

`backend/.env` is gitignored. Never commit real API keys. The committed `backend/.env.example` only documents the variable names.
