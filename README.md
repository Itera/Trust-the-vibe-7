# HuMotivatoren™

Itera Internal Motivation Consulting — a satirical-but-warm inspiration tool.
You tell it what you're about to do; it returns a "Motivation Dose" deck: persona-voiced
pep talk, quote, useless fact, fake KPI, advice, cat image, haiku, and more.

- **Frontend**: Vite + React + TypeScript — persona-themed deck UI.
- **Backend**: FastAPI — orchestrates Azure OpenAI (gpt-4o-mini) + 5 free open APIs, and also serves the built frontend.
- **Values guardrail** baked into the system prompt: warm, cheeky, never mean, no politics/religion/stereotypes.

## Stack at a glance

```
            ┌───────────────────────────────┐
 User  ───▶ │  Vite / React  (frontend)     │
            │  /src/components/Motivator    │
            └──────────────┬────────────────┘
                           │  POST /api/motivate
                           ▼
            ┌───────────────────────────────┐
            │  FastAPI  (backend)           │
            │  orchestrator.py              │
            │   • gathers open APIs in      │
            │     parallel (httpx)          │
            │   • feeds raw materials +     │
            │     persona to Azure OpenAI   │
            │   • returns MotivationPackage │
            └───────────────────────────────┘
                │          │            │
      quotable.io    uselessfacts   adviceslip.com
      numbersapi.com      thecatapi.com
```

## Prerequisites

- Python **3.10+** ([python.org](https://www.python.org/downloads/))
- Node **18+** ([nodejs.org](https://nodejs.org/))

## Quick start (macOS, Linux, Windows — identical)

```bash
# 1. install deps + build frontend
python scripts/setup.py

# 2. run everything (UI + API at http://127.0.0.1:8000)
python scripts/start.py

# 3. tests
python scripts/test.py
```

> Windows: if `python` isn't on PATH, use `py -3 scripts/setup.py` etc.

## Configuration

`backend/.env` is gitignored. See `backend/.env.example` for required variables:

```
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com
AZURE_OPENAI_DEPLOYMENT=gpt-4o-mini
AZURE_OPENAI_API_VERSION=2025-01-01-preview
AZURE_OPENAI_API_KEY=your-key-here
ALLOWED_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
```

Project `.env` wins over shell env vars (so a random exported `AZURE_OPENAI_API_KEY` from your shell can't silently override local config).

## API

| Endpoint | Purpose |
| --- | --- |
| `POST /api/motivate` | Body: `{ task, persona, language, seriousness, cards[] }` → `MotivationPackage` |
| `GET /api/personas?language=` | List of personas with tagline + accent color |
| `GET /api/health` | `{status: "ok"}` |

Interactive docs at <http://127.0.0.1:8000/docs>.

## Extending (good PR slots for team members)

### Add a new card kind

1. Add the literal to `backend/app/schemas.py:CardKind` and include it in `DEFAULT_CARDS` if on by default.
2. If it needs external data, add a client in `backend/app/apis/` and wire it in `orchestrator.gather_raw_materials`.
3. Add a description line in `orchestrator._card_menu` for both languages.
4. Register an entry in `frontend/src/personas.ts` (`ALL_CARD_KINDS`, `CARD_LABELS_EN/NO`).
5. (Optional) Give it a size in `frontend/src/components/MotivationCard.tsx:SIZE_BY_KIND`.
6. Write a test for any new backend client with respx.

### Add a new persona

1. Add an entry to `backend/app/personas.py:PERSONAS` with `voice_en`, `voice_no`, tagline, and accent color.
2. Add a matching entry in `frontend/src/personas.ts:PERSONA_THEMES` (fonts + colors).
3. Extend the `PersonaKey` literal in both `backend/app/schemas.py` and `frontend/src/types.ts`.
4. That's it — it shows up in the settings bar automatically.

### Other good team-PR slices

- **Audio layer** — fanfare/applause sfx on dose completion, or TTS of the pep talk.
- **Share as PNG** — render the report card to an image with `html-to-image`.
- **New open API** — Spotify (tracks), NASA APOD (visuals), open-meteo (weather card).
- **Fake testimonial generator** — pure LLM card kind, zero API needed.
- **Playlist card** — LLM generates 3 fake-song titles + fake artists, formatted as a Spotify-ish block.

## Layout

```
.
├── backend/
│   ├── app/
│   │   ├── main.py           FastAPI entrypoint + static-mount for frontend/dist
│   │   ├── orchestrator.py   The brain: parallel fetch → LLM compose
│   │   ├── llm.py            Azure OpenAI client (httpx)
│   │   ├── personas.py       Persona definitions (NO + EN voices)
│   │   ├── schemas.py        MotivationRequest, MotivationPackage, Card, ...
│   │   ├── config.py         pydantic-settings, .env wins over shell
│   │   └── apis/             One file per open API
│   └── tests/                pytest (27 tests)
├── frontend/
│   ├── src/
│   │   ├── components/       Motivator, HeroInput, SettingsBar, MotivationCard, LoadingState
│   │   ├── personas.ts       Client-side persona themes + card labels
│   │   ├── api.ts            typed client
│   │   └── types.ts
│   └── src/__tests__/        vitest (9 tests)
├── scripts/                  setup.py, start.py, test.py (cross-platform)
└── README.md
```

## Demo (2 minutes on a big screen)

1. Open <http://127.0.0.1:8000> — big "HuMotivatoren™" header.
2. Click the **Read the news** quick pick → **DOSE ME**. Watch the loading messages rotate.
3. The deck materialises with a hero pep talk, quote, KPI, cat picture, haiku, advice.
4. Switch persona to **Gremlin** → hit **Another dose** on the same task. Same materials, wildly different voice.
5. Click **NO** to flip the whole UI to Norwegian. Re-dose to show bilingual output.
6. End on the "Ragulan vil jeg skal spille fotball" quick pick for the comedy beat.

## Secrets

`backend/.env` is gitignored. Never commit real API keys. Rotate the Azure key if it's ever been pasted into chat/terminal history.
