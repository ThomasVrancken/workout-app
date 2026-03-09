# Workout Agent

An AI-powered workout coach that connects to your [Hevy](https://www.hevyapp.com/) workout data. Chat with an agent that can look up your workout history, analyse trends, and create or modify routines on your behalf.

## Architecture

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

A single Cloud Run service serves both the static chat UI and the API backend. The agent uses MCP (Model Context Protocol) to communicate with the Hevy API through the [hevy-mcp](https://www.npmjs.com/package/hevy-mcp) server.

## Tech Stack

| Component | Choice |
|-----------|--------|
| Backend | Python 3.12 + FastAPI |
| LLM | Gemini 3 Flash (via Vertex AI) |
| MCP server | [hevy-mcp](https://www.npmjs.com/package/hevy-mcp) (Node.js, spawned as subprocess) |
| Frontend | Single HTML file (vanilla JS, no build step) |
| Hosting | Google Cloud Run (serverless, scales to zero) |
| Infrastructure | Terraform |

## Prerequisites

- A [Google Cloud](https://cloud.google.com/) account with billing enabled
- [gcloud CLI](https://cloud.google.com/sdk/docs/install) installed and authenticated
- [Terraform](https://developer.hashicorp.com/terraform/install) >= 1.5
- A [Hevy](https://www.hevyapp.com/) account and API key

## Quick Start

```bash
# 1. Clone the repo
git clone https://github.com/your-username/workout-app.git
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

## Local Development

```bash
# Create a .env file from the example
cp infra/terraform.tfvars.example .env
# Edit .env to use KEY=VALUE format (see docs/DEPLOY.md for details)

# Install dependencies
uv venv && source .venv/bin/activate
uv pip install -e .

# Run the server
uv run uvicorn app.main:app --host 0.0.0.0 --port 8080 --reload
```

Open http://localhost:8080 in your browser. Node.js is required locally for the `hevy-mcp` subprocess.

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
├── infra/                       # Terraform (infrastructure)
│   ├── main.tf              # Provider + API enablements
│   ├── iam.tf               # Service account + IAM
│   ├── cloud_run.tf         # Artifact Registry + Cloud Run
│   ├── variables.tf         # Input variables
│   ├── outputs.tf           # Outputs (URL, image path)
│   └── terraform.tfvars.example
├── deploy.sh                # Build + deploy script
├── Dockerfile
├── pyproject.toml
└── docs/
    └── DEPLOY.md            # Detailed deployment guide
```
