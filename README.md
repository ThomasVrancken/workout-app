# Workout Agent

An AI workout coach that already knows your training history.

Your workout app tracks reps. But fitness is messy — you tweak a shoulder, you play other sports, your goals shift. Workout Agent reads your [Hevy](https://www.hevyapp.com/) data and chats with you about it. Ask anything, adjust your routine on the fly, and skip the part where you re-explain your training background to a generic AI every time.

> **Live app:** [`https://workout-agent.app`](https://workout-agent.app) *(replace with your deployment URL)*
>
> **Demo:** *(2-minute Loom video — add link once recorded)*

---

# For users

## What it does

- Reads your Hevy workouts and routines.
- Modifies your routines for you when you ask (e.g. "swap dumbbell press for incline barbell on push day").
- Knows exercise science, sports physiology, and which muscle groups your other activities use.
- Lives as a **PWA** — works in the browser and installs to your phone's home screen like a native app.

## Getting started (2 minutes)

1. **Open the app** and sign in with your Google account (or create an email/password account).
2. **Accept the Privacy Policy and Terms**.
3. **Connect your Hevy account.** Open [hevy.com/settings?developer](https://hevy.com/settings?developer), generate an API key, and paste it into the onboarding screen. The key is encrypted before being stored — only the server, never the browser, can decrypt it to call Hevy on your behalf.
4. **Ask anything.** Some examples to try first:
   - "Show me my last workout."
   - "Why has my bench press stalled the last 3 weeks?"
   - "I tweaked my shoulder — adjust my push day."
   - "I'm playing squash twice this week. Reduce my leg volume accordingly."
   - "Build me a new push/pull/legs routine focused on hypertrophy."

## Install it on your phone

On iPhone (Safari) or Android (Chrome), open the app and choose **Add to Home Screen** in the share menu. It opens full-screen, no browser chrome.

## FAQ

**Do I need a Hevy account?**
Yes. Hevy is where your workout data lives. The app reads from your Hevy account through their official API.

**Do I need a Hevy PRO subscription?**
Yes. Hevy's API access requires the PRO plan. There's no way around this — it's a Hevy policy, not ours.

**Is my data safe?**
Your Hevy API key is encrypted at rest with a server-side key (Fernet / AES-128). Your chat messages are **not** stored on the server. You can export everything we have on you or delete your account at any time from settings. See the [Privacy Policy](app/static/privacy.html).

**Is it free?**
Yes. It's an open-source pet project. Cloud Run costs are negligible.

**How do I delete my account?**
Open the app → settings (gear icon) → "Delete my account". Everything is removed immediately and permanently.

**Can the AI mess up my routines in Hevy?**
The AI can modify your routines via the Hevy API. If you don't like a change, you can revert it inside the Hevy app, or revoke the API key in Hevy settings at any time.

---

# For developers

## Two ways to run this code

### A. Use the MCP server only (no deployment)

The [`hevy-mcp`](https://www.npmjs.com/package/hevy-mcp) npm package is the open-source MCP server that powers the Hevy integration. You can wire it up directly to any MCP client (Cursor, Claude Desktop, Claude Code, Windsurf, etc.) without running this repo at all.

#### Cursor / Claude Desktop config

```json
{
  "mcpServers": {
    "hevy-mcp": {
      "command": "npx",
      "args": ["-y", "hevy-mcp"],
      "env": { "HEVY_API_KEY": "<your-hevy-api-key>" }
    }
  }
}
```

For Claude Desktop, the config file is at `~/Library/Application Support/Claude/claude_desktop_config.json` on macOS.

#### Claude Code

```bash
claude mcp add hevy-mcp -- npx -y hevy-mcp --hevy-api-key=<your-hevy-api-key>
```

#### Other MCP clients

Runs over stdio. Launch with `HEVY_API_KEY=… npx -y hevy-mcp` and point your MCP client at it.

### B. Fork and host your own instance

Deploy your own multi-user PWA on Google Cloud Run with Firebase Auth and Firestore.

See [`docs/DEPLOY.md`](docs/DEPLOY.md) for the full step-by-step guide. Short version:

```bash
git clone https://github.com/ThomasVrancken/workout-app.git
cd workout-app

# 1. Authenticate with GCP
gcloud auth login
gcloud auth application-default login

# 2. Set up Firebase Auth (Google + email/password) in the Firebase Console
# 3. Generate an encryption key:
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"

# 4. Configure Terraform
cd infra
cp terraform.tfvars.example terraform.tfvars
# Edit with your project_id, Firebase config, encryption key

# 5. Provision infrastructure
terraform init
terraform apply

# 6. Build and deploy
cd ..
./deploy.sh
```

## Architecture

```
┌──────────────┐       HTTPS        ┌────────────────────────────────────────────┐
│   Phone /    │  ◄──────────────►  │   Google Cloud Run (one service)           │
│   Browser    │                    │                                            │
│              │                    │  ┌──────────────┐    ┌────────────────┐    │
│  Landing /   │                    │  │   FastAPI    │───►│  hevy-mcp      │    │
│  Chat PWA    │                    │  │  (Python)    │    │  (Node sub-    │    │
│              │                    │  │              │    │   process,     │    │
│              │                    │  │              │    │   per request) │    │
└──────┬───────┘                    │  └──────┬───────┘    └────────────────┘    │
       │                            │         │                                  │
       │ Firebase Auth (ID token)   │         ├──► Firestore (encrypted user data)
       │                            │         ├──► Vertex AI / Gemini             │
       │                            │         └──► Firebase Auth (verify tokens)  │
       │                            └────────────────────────────────────────────┘
       │
       └──► Firebase Auth (Google Sign-In / email & password)
```

### Tech stack

| Component       | Choice                                                          |
| --------------- | --------------------------------------------------------------- |
| Backend         | Python 3.12 + FastAPI                                           |
| Auth            | Firebase Auth (Google SSO + email/password)                     |
| Database        | Firestore (Native mode)                                         |
| Encryption      | `cryptography.fernet` (AES-128) for the per-user Hevy API key   |
| LLM             | Gemini 3 Flash via Vertex AI                                    |
| MCP server      | [`hevy-mcp`](https://www.npmjs.com/package/hevy-mcp) (Node.js, spawned per request) |
| Frontend        | Vanilla HTML / CSS / JS (no build step)                         |
| Hosting         | Google Cloud Run (scales to zero)                               |
| Infrastructure  | Terraform                                                       |

### Request flow (chat)

1. Browser sends a chat message with the user's Firebase ID token.
2. FastAPI verifies the token, looks up the user in Firestore, decrypts their Hevy API key in memory.
3. FastAPI spawns a short-lived `hevy-mcp` subprocess with that user's key.
4. Gemini drives a tool-use loop against the MCP server.
5. The subprocess exits and the request completes.

Chat history is held only in the browser — it is never persisted server-side.

## Project structure

```
workout-app/
├── app/
│   ├── main.py              # FastAPI routes (landing, chat, /api/me, etc.)
│   ├── agent.py             # Per-request MCP subprocess + Gemini tool loop
│   ├── auth.py              # Firebase ID token verification
│   ├── users.py             # Firestore user store + Fernet encryption helpers
│   ├── system_prompt.txt    # Agent system prompt
│   └── static/
│       ├── landing.html     # Public marketing landing page (/)
│       ├── index.html       # Chat PWA (/app)
│       ├── privacy.html     # Privacy Policy (/privacy)
│       ├── terms.html       # Terms of Service (/terms)
│       ├── manifest.json    # PWA manifest
│       └── sw.js            # Service worker
├── infra/                   # Terraform (GCP infrastructure)
│   ├── main.tf              # Provider, API enablements, Firestore + rules
│   ├── iam.tf               # Service account + IAM
│   ├── cloud_run.tf         # Artifact Registry + Cloud Run
│   ├── variables.tf         # Input variables
│   ├── outputs.tf           # Outputs (URL, image path)
│   ├── firestore.rules      # Client-side Firestore is locked down
│   └── terraform.tfvars.example
├── docs/
│   ├── DEPLOY.md            # Full deployment guide
│   └── PROMOTION.md         # Social media post templates + demo script
├── scripts/
│   └── get_latest_workout.py
├── deploy.sh
├── Dockerfile
├── pyproject.toml
└── README.md
```

## Contributing

This is a personal pet project, but PRs and issues are welcome.

- For bugs or feature requests, open an issue.
- For changes, please open a PR against `main`. Keep changes focused and explain the motivation in the PR description.
- Keep the frontend dependency-free (no npm build step).

## License

Provided as-is for personal use. The [`hevy-mcp`](https://github.com/chrisdoc/hevy-mcp) server is an MIT-licensed open-source package by [Christoph Kieslich](https://github.com/chrisdoc).
