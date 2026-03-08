# Plan: Mobile Workout Chat Agent

## Goal

Build a mobile-friendly chat interface that lets you talk to an AI agent with full access to your Hevy workout data — from your phone, without opening Cursor.

## Architecture Overview

```
┌──────────────┐       HTTPS        ┌─────────────────────────────────┐
│   Phone      │  ◄──────────────►  │   Google Cloud Run              │
│   (browser)  │                    │                                 │
│              │                    │  ┌───────────┐   ┌───────────┐  │
│  PWA chat UI │                    │  │  FastAPI   │   │ hevy-mcp  │  │
│              │                    │  │  backend   ├──►│ (subprocess│  │
│              │                    │  │            │   │  via stdio)│  │
│              │                    │  └─────┬──────┘   └───────────┘  │
└──────────────┘                    │        │                        │
                                    │        │ Gemini API             │
                                    │        ▼ (via Vertex AI)        │
                                    │  ┌───────────┐                  │
                                    │  │  Gemini 3  │                  │
                                    │  │   Flash    │                  │
                                    │  └───────────┘                  │
                                    └─────────────────────────────────┘
```

**Single Cloud Run service** serves both the static chat UI and the API backend.

## Stack Choices

| Component        | Choice               | Why                                                        |
| ---------------- | -------------------- | ---------------------------------------------------------- |
| Backend          | Python + FastAPI     | Matches existing project (Python 3.12, uv)                 |
| MCP integration  | `mcp` Python SDK     | Spawns `hevy-mcp` as subprocess, auto-discovers all tools  |
| LLM              | Gemini 3 Flash (Vertex AI) | Strong tool-use, included in your GCP project, no extra API key |
| Frontend         | Single HTML file (vanilla JS) | No build step, served as static file by FastAPI   |
| Hosting          | Google Cloud Run     | Serverless, scales to zero, you already have a GCP project |
| Container        | Docker (Python + Node.js) | Node.js needed for `npx hevy-mcp`                    |
| Auth             | Simple shared secret | Just you using it — a password in a header/cookie suffices |

## Project Structure

```
workout-app/
├── app/
│   ├── main.py              # FastAPI app: chat endpoint + static file serving
│   ├── agent.py             # MCP client + Claude tool-use loop
│   ├── auth.py              # Simple shared-secret auth middleware
│   └── static/
│       └── index.html       # Chat PWA (single file: HTML + CSS + JS)
├── Dockerfile               # Python 3.12 + Node.js runtime
├── docs/
│   ├── PROJECT.md
│   └── PLAN.md              # This file
├── scripts/
│   └── get_latest_workout.py
├── pyproject.toml            # Updated with new dependencies
├── .env                      # Local secrets (HEVY_API_KEY, GOOGLE_CLOUD_PROJECT, APP_SECRET)
└── .gitignore
```

## Detailed Design

### 1. MCP Client (`app/agent.py`)

Uses the Python `mcp` SDK to spawn `hevy-mcp` as a child process over stdio:

```python
from mcp.client.stdio import stdio_client, StdioServerParameters
from mcp.client.session import ClientSession

server_params = StdioServerParameters(
    command="npx",
    args=["-y", "hevy-mcp"],
    env={"HEVY_API_KEY": os.environ["HEVY_API_KEY"]},
)

async with stdio_client(server_params) as (read, write):
    async with ClientSession(read, write) as session:
        await session.initialize()
        tools = await session.list_tools()
        # Convert MCP tools → Gemini function declarations
        # Run the agentic loop
```

The **agentic loop** (using `google-genai` SDK):
1. Send user message + function declarations to Gemini API
2. If Gemini responds with function calls → execute them via `session.call_tool()`
3. Feed function responses back to Gemini
4. Repeat until Gemini produces a final text response
5. Return the text response to the user

```python
from google import genai
from google.genai import types

client = genai.Client()  # Uses GOOGLE_CLOUD_PROJECT + GOOGLE_GENAI_USE_VERTEXAI=True

response = client.models.generate_content(
    model="gemini-3-flash-preview",
    contents=conversation_history,
    config=types.GenerateContentConfig(tools=[tool_declarations]),
)
```

We keep the MCP session alive for the lifetime of the Cloud Run instance (not per-request) to avoid the ~2s cold start of `npx hevy-mcp` on every message.

### 2. API Backend (`app/main.py`)

A minimal FastAPI app with two responsibilities:

**Endpoints:**
- `GET /` → Serves the static chat UI (`index.html`)
- `POST /api/chat` → Accepts `{ "message": "...", "history": [...] }`, returns `{ "response": "..." }`
- `GET /api/health` → Health check for Cloud Run

**Lifecycle:**
- On startup: spawn the MCP server subprocess, initialize the session, cache tool definitions
- On shutdown: cleanly close the MCP session

### 3. Auth (`app/auth.py`)

Since this is a personal app, simple shared-secret auth:

- You choose a secret passphrase (e.g. `my-workout-bot-2026`) and set it as the `APP_SECRET` env var
- **First visit on your phone**: You open the Cloud Run URL, the app shows a simple "Enter passphrase" screen
- You type the passphrase once → it's saved in your browser's `localStorage`
- From then on, the app loads directly into the chat — no login screen
- Every `/api/chat` request includes the passphrase as a `Bearer` token in the `Authorization` header
- FastAPI middleware rejects requests without a valid token (returns 401)
- If you ever clear browser data, you just re-enter the passphrase once

This is sufficient for a personal tool. No user accounts, no OAuth. The passphrase
prevents random people from hitting your endpoint and burning your Gemini quota.

### 4. Chat UI (`app/static/index.html`)

A single HTML file with embedded CSS and JS — no build tooling.

**Features:**
- Mobile-first responsive design
- Chat bubbles (user vs. assistant)
- Input bar fixed at bottom (like any chat app)
- "Add to Home Screen" PWA manifest so it feels like a native app
- On first visit, prompts for the shared secret and stores it
- Shows a typing indicator while the agent is working
- Markdown rendering for assistant responses (lightweight, e.g. marked.js via CDN)

### 5. Docker Container (`Dockerfile`)

```dockerfile
FROM python:3.12-slim

# Install Node.js (needed for npx hevy-mcp)
RUN apt-get update && apt-get install -y curl \
    && curl -fsSL https://deb.nodesource.com/setup_22.x | bash - \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY pyproject.toml .
RUN pip install .
COPY app/ app/

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
```

### 6. Deployment (Google Cloud Run)

```bash
# One-time setup
gcloud run deploy workout-agent \
  --source . \
  --region europe-west1 \
  --allow-unauthenticated \
  --set-env-vars "HEVY_API_KEY=...,GOOGLE_CLOUD_PROJECT=...,APP_SECRET=..."
```

Cloud Run will build the Docker image via Cloud Build and deploy it. The `--allow-unauthenticated` flag is fine because we handle auth at the application level with the shared secret.

On Cloud Run, the service automatically has a Vertex AI-enabled service account, so no API key is needed for Gemini — it uses Application Default Credentials.

## Implementation Steps

### Phase 1: Local working prototype
1. **Set up dependencies** — Add `mcp`, `google-genai`, `fastapi`, `uvicorn` to `pyproject.toml`
2. **Build `app/agent.py`** — MCP client + Gemini agentic tool-use loop
3. **Build `app/main.py`** — FastAPI endpoints
4. **Build `app/auth.py`** — Shared-secret middleware
5. **Build `app/static/index.html`** — Chat PWA UI
6. **Test locally** — Run with `uvicorn`, test from browser

### Phase 2: Containerize and deploy
7. **Write `Dockerfile`** — Python + Node.js multi-runtime image
8. **Test with Docker locally** — `docker build && docker run`
9. **Deploy to Cloud Run** — `gcloud run deploy`
10. **Test from phone** — Open the Cloud Run URL, add to home screen

## Secrets & Environment Variables

| Variable                  | Where it lives                    | Purpose                              |
| ------------------------- | --------------------------------- | ------------------------------------ |
| `HEVY_API_KEY`            | `.env` (local), Cloud Run env var | Hevy API authentication              |
| `GOOGLE_CLOUD_PROJECT`    | `.env` (local), Cloud Run env var | GCP project for Vertex AI            |
| `GOOGLE_GENAI_USE_VERTEXAI` | `.env` (local), Cloud Run env var | Tells google-genai SDK to use Vertex AI |
| `APP_SECRET`              | `.env` (local), Cloud Run env var | Shared passphrase for app auth       |

## Cost Estimate

- **Cloud Run**: Free tier covers ~2M requests/month. With scale-to-zero, you pay nothing when not chatting.
- **Gemini 3 Flash**: Very cheap via Vertex AI — included in GCP billing. Personal use will be pennies/month.
- **Total**: Effectively free for personal use.

## Decisions

1. **Region**: `europe-west1` (Belgium)
2. **Conversation memory**: No persistence for v1 — each conversation starts fresh
3. **System prompt**: Stored in `app/system_prompt.txt` — editable directly in the repo
