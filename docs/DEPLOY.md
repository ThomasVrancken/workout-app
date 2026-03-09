# Deployment Guide

Step-by-step instructions for deploying the Workout Agent to Google Cloud Run.

## 1. Prerequisites

### Google Cloud account

1. Create a GCP account at https://cloud.google.com/ if you don't have one
2. Create a new project (or use an existing one) at https://console.cloud.google.com/projectcreate
3. Make sure billing is enabled for the project at https://console.cloud.google.com/billing

> **Cost**: Cloud Run scales to zero and Gemini 3 Flash is very cheap via Vertex AI. Personal use will cost pennies per month at most.

### Install the gcloud CLI

Follow the instructions at https://cloud.google.com/sdk/docs/install for your OS, then:

```bash
gcloud auth login
gcloud auth application-default login
```

### Install Terraform

Follow the instructions at https://developer.hashicorp.com/terraform/install for your OS. Verify with:

```bash
terraform --version   # Should be >= 1.5
```

### Get a Hevy API key

1. Open the Hevy app or go to https://www.hevyapp.com/
2. Navigate to your account settings: https://hevy.com/settings?developer
3. Generate an API key and store it locally

## 2. Configure

```bash
cd infra
cp terraform.tfvars.example terraform.tfvars
```

Edit `terraform.tfvars` with your values:

```hcl
project_id   = "my-gcp-project-123"    # Your GCP project ID
region       = "europe-west1"           # GCP region (pick one close to you)
hevy_api_key = "hvy_abc123..."          # Your Hevy API key
app_secret   = "my-secret-passphrase"   # You'll type this to log in to the chat
gemini_model = "gemini-3-flash"         # Or another Gemini model
```

Common regions: `europe-west1` (Belgium), `us-central1` (Iowa), `asia-northeast1` (Tokyo).

## 3. Provision infrastructure

```bash
cd infra
terraform init
terraform apply
```

Terraform creates the GCP infrastructure:
1. Enables the required APIs (Vertex AI, Cloud Run, Cloud Build, Artifact Registry)
2. Creates a least-privilege service account for the app
3. Creates an Artifact Registry Docker repository
4. Creates the Cloud Run service (with a placeholder image, configured with your env vars and service account)
5. Sets up public access (the app handles authentication internally via the passphrase)

When it finishes, it will print the service URL. The service won't be functional yet -- the actual app image is deployed in the next step.

## 4. Build and deploy the app

From the repo root:

```bash
./deploy.sh
```

This script:
1. Reads the project ID, region, and image path from Terraform state
2. Builds the Docker image using Cloud Build
3. Deploys it to the Cloud Run service

When it finishes, it prints the live service URL. Open it in your browser, enter your passphrase, and start chatting.

## 5. Updating the app

After making code changes, just re-run the deploy script:

```bash
./deploy.sh
```

This rebuilds the image and deploys a new Cloud Run revision. You do **not** need to re-run `terraform apply` unless you've changed infrastructure configuration (e.g. env vars, region, service account roles).

## 7. Tearing down

To remove all GCP resources created by Terraform:

```bash
cd infra
terraform destroy
```

This deletes the Cloud Run service, service account, Artifact Registry repository, and IAM bindings. It does **not** disable the APIs (to avoid breaking other services in your project).

## 8. Importing existing resources

If you've already deployed manually with `gcloud` commands and want to bring your existing infrastructure under Terraform management, import each resource before running `terraform apply`:

```bash
cd infra
terraform init

# Import API enablements
terraform import 'google_project_service.apis["aiplatform.googleapis.com"]' PROJECT_ID/aiplatform.googleapis.com
terraform import 'google_project_service.apis["run.googleapis.com"]' PROJECT_ID/run.googleapis.com
terraform import 'google_project_service.apis["cloudbuild.googleapis.com"]' PROJECT_ID/cloudbuild.googleapis.com
terraform import 'google_project_service.apis["artifactregistry.googleapis.com"]' PROJECT_ID/artifactregistry.googleapis.com

# Import service account
terraform import google_service_account.workout_agent projects/PROJECT_ID/serviceAccounts/workout-agent-sa@PROJECT_ID.iam.gserviceaccount.com

# Import IAM binding
terraform import google_project_iam_member.vertex_ai_user "PROJECT_ID roles/aiplatform.user serviceAccount:workout-agent-sa@PROJECT_ID.iam.gserviceaccount.com"

# Import Artifact Registry repository (if it exists)
terraform import google_artifact_registry_repository.app projects/PROJECT_ID/locations/REGION/repositories/workout-agent

# Import Cloud Run service
terraform import google_cloud_run_v2_service.workout_agent projects/PROJECT_ID/locations/REGION/services/workout-agent
```

Replace `PROJECT_ID` with your GCP project ID and `REGION` with your region (e.g. `europe-west1`).

After importing, run `terraform plan` to verify there are no unexpected changes before applying.

## Local Development

For running locally (without deploying to Cloud Run):

1. Create a `.env` file in the project root:

```
HEVY_API_KEY=your-hevy-api-key
GOOGLE_CLOUD_PROJECT=your-project-id
GOOGLE_CLOUD_LOCATION=your-project-location
GEMINI_MODEL=gemini-3-flash
APP_SECRET=your-passphrase
```

2. Install Python dependencies:

```bash
uv venv && source .venv/bin/activate
uv pip install -e .
```

3. Make sure Node.js is installed (needed for the `hevy-mcp` subprocess).

4. Run the dev server:

```bash
uv run uvicorn app.main:app --host 0.0.0.0 --port 8080 --reload
```

5. Open http://localhost:8080
