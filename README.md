# Workout Agent

An AI-powered workout coach that connects to your [Hevy](https://www.hevyapp.com/) workout data. Chat with an agent that can look up your workout history, analyse trends, and create or modify routines on your behalf.

> **Requires a [Hevy](https://www.hevyapp.com/) account with a PRO subscription** (needed for API access).

## Two Ways to Use This

### Option A: MCP Server Only (Quickest)

Use the [`hevy-mcp`](https://www.npmjs.com/package/hevy-mcp) server directly with any MCP-compatible AI tool — no deployment needed. Your AI assistant gets full access to your Hevy workout data through the Model Context Protocol.

Works with tools like **Cursor**, **Claude Code**, **Claude Desktop**, **Windsurf**, and any other MCP client.

**[Jump to MCP setup instructions](#option-a-mcp-server-setup)**

### Option B: Deploy the Full Application

Deploy a self-hosted workout chat agent as a web app (PWA). This gives you a dedicated mobile-friendly chat UI powered by Gemini, hosted on Google Cloud Run.

**[Jump to deployment instructions](#option-b-full-application-deployment)**

---

## Option A: MCP Server Setup

The [`hevy-mcp`](https://www.npmjs.com/package/hevy-mcp) npm package is a ready-made MCP server that gives any AI assistant access to your Hevy data — workouts, routines, exercises, and more.

### Prerequisites

- **Node.js** >= 20 installed
- A **Hevy API key** — get one at [hevy.com/settings?developer](https://hevy.com/settings?developer)

### Cursor

Add the following to your MCP config file (`.cursor/mcp.json` in your project, or `~/.cursor/mcp.json` globally):

```json
{
  "mcpServers": {
    "hevy-mcp": {
      "command": "npx",
      "args": ["-y", "hevy-mcp"],
      "env": {
        "HEVY_API_KEY": "<your-hevy-api-key>"
      }
    }
  }
}
```

### Claude Desktop

Add to your Claude Desktop config (`~/Library/Application Support/Claude/claude_desktop_config.json` on macOS):

```json
{
  "mcpServers": {
    "hevy-mcp": {
      "command": "npx",
      "args": ["-y", "hevy-mcp"],
      "env": {
        "HEVY_API_KEY": "<your-hevy-api-key>"
      }
    }
  }
}
```

### Claude Code

```bash
claude mcp add hevy-mcp -- npx -y hevy-mcp --hevy-api-key=<your-hevy-api-key>
```

### Other MCP Clients

The server runs over **stdio** transport. Launch it with:

```bash
HEVY_API_KEY=<your-hevy-api-key> npx -y hevy-mcp
```

Point your MCP client's stdio configuration at this command.

### What You Can Do

Once connected, your AI assistant can use these tools:

| Category | Tools |
|----------|-------|
| **Workouts** | Fetch workout history, get a specific workout, create/update workouts, get workout count |
| **Routines** | List routines, get/create/update routines |
| **Exercises** | Browse exercise templates, get exercise history |
| **Folders** | Manage routine folders |

Example prompts:
- *"Show me my last 5 workouts"*
- *"What's my bench press progression over the last month?"*
- *"Update my Full Body routine to add Romanian deadlifts"*
- *"Create a new push/pull/legs routine for me"*

---

## Option B: Full Application Deployment

Deploy a standalone workout chat agent as a PWA (Progressive Web App) on Google Cloud Run. This gives you a mobile-friendly chat interface you can add to your home screen.

### Architecture

```
┌──────────────┐       HTTPS        ┌─────────────────────────────────┐
│   Phone /    │  ◄──────────────►  │   Google Cloud Run              │
│   Browser    │                    │                                 │
│              │                    │  ┌───────────┐   ┌───────────┐  │
│  Chat UI     │                    │  │  FastAPI   │   │ hevy-mcp  │  │
│  (PWA)       │                    │  │  backend   ├──►│(subprocess│  │
│              │                    │  │            │   │ via stdio)│  │
│              │                    │  └─────┬──────┘   └───────────┘  │
└──────────────┘                    │        │                        │
                                    │        │ Gemini API             │
                                    │        ▼ (Vertex AI)            │
                                    │  ┌───────────┐                  │
                                    │  │  Gemini 3  │                  │
                                    │  │   Flash    │                  │
                                    │  └───────────┘                  │
                                    └─────────────────────────────────┘
```

A single Cloud Run service serves both the static chat UI and the API backend. The agent uses the `hevy-mcp` server (spawned as a subprocess) and Gemini for tool-calling and conversation.

### Tech Stack

| Component | Choice |
|-----------|--------|
| Backend | Python 3.12 + FastAPI |
| LLM | Gemini 3 Flash (via Vertex AI) |
| MCP server | [hevy-mcp](https://www.npmjs.com/package/hevy-mcp) (Node.js, spawned as subprocess) |
| Frontend | Single HTML file (vanilla JS, no build step) |
| Hosting | Google Cloud Run (serverless, scales to zero) |
| Infrastructure | Terraform |

### Prerequisites

- A [Google Cloud](https://cloud.google.com/) account with billing enabled
- [gcloud CLI](https://cloud.google.com/sdk/docs/install) installed and authenticated
- [Terraform](https://developer.hashicorp.com/terraform/install) >= 1.5
- A [Hevy](https://www.hevyapp.com/) account and API key

### Quick Start

```bash
# 1. Clone the repo
git clone https://github.com/ThomasVrancken/workout-app.git
cd workout-app

# 2. Authenticate with GCP
gcloud auth login
gcloud auth application-default login

# 3. Configure your deployment
cd infra
cp terraform.tfvars.example terraform.tfvars
# Edit terraform.tfvars with your project ID, API keys, and passphrase

# 4. Provision infrastructure
terraform init
terraform apply

# 5. Build and deploy the app
cd ..
./deploy.sh
```

Step 4 creates the GCP infrastructure (APIs, service account, Artifact Registry, Cloud Run service). Step 5 builds the Docker image and deploys it. After code changes, only step 5 needs to be re-run.

For detailed instructions (GCP project setup, getting a Hevy API key, troubleshooting), see [docs/DEPLOY.md](docs/DEPLOY.md).

### Local Development

```bash
# Create a .env file from the example
cp infra/terraform.tfvars.example .env
# Edit .env to use KEY=VALUE format (see docs/DEPLOY.md for details)

# Install dependencies (requires uv: https://docs.astral.sh/uv/)
uv venv && source .venv/bin/activate
uv pip install -e .

# Run the server (Node.js required for the hevy-mcp subprocess)
uv run uvicorn app.main:app --host 0.0.0.0 --port 8080 --reload
```

Open http://localhost:8080 in your browser.

### Cost

Cloud Run scales to zero and Gemini 3 Flash via Vertex AI is very cheap. Personal use costs pennies per month at most.

---

## Project Structure

```
workout-app/
├── app/
│   ├── main.py              # FastAPI app: endpoints + static serving
│   ├── agent.py             # MCP client + Gemini tool-use loop
│   ├── auth.py              # Shared-secret auth middleware
│   ├── system_prompt.txt    # Agent system prompt
│   └── static/
│       └── index.html       # Chat PWA (HTML + CSS + JS)
├── infra/                   # Terraform (GCP infrastructure)
│   ├── main.tf              # Provider + API enablements
│   ├── iam.tf               # Service account + IAM
│   ├── cloud_run.tf         # Artifact Registry + Cloud Run
│   ├── variables.tf         # Input variables
│   ├── outputs.tf           # Outputs (URL, image path)
│   └── terraform.tfvars.example
├── scripts/
│   └── get_latest_workout.py  # CLI helper to fetch latest workout
├── deploy.sh                # Build + deploy script
├── Dockerfile
├── pyproject.toml
└── docs/
    ├── DEPLOY.md            # Detailed deployment guide
    └── PLAN.md              # Architecture design notes
```

## License

This project is provided as-is for personal use. The [`hevy-mcp`](https://github.com/chrisdoc/hevy-mcp) server is an MIT-licensed open source package by [Christoph Kieslich](https://github.com/chrisdoc).
