# Deployment Guide

Step-by-step instructions for deploying your own instance of Workout Agent to Google Cloud Run.

> If you just want to **use** the public Workout Agent, you don't need any of this — open the live URL and sign in. This guide is for self-hosters and contributors.

## 1. Prerequisites

### Google Cloud account

1. Create a GCP account at https://cloud.google.com/ if you don't have one.
2. Create a new project (or use an existing one) at https://console.cloud.google.com/projectcreate.
3. Make sure billing is enabled at https://console.cloud.google.com/billing.

> **Cost.** Cloud Run scales to zero, Firestore has a generous free tier, and Gemini 3 Flash is very cheap via Vertex AI. A small personal deployment will cost roughly pennies per month.

### gcloud CLI

Follow https://cloud.google.com/sdk/docs/install, then:

```bash
gcloud auth login
gcloud auth application-default login
```

### Terraform

Follow https://developer.hashicorp.com/terraform/install (>= 1.5).

### Set up Firebase Authentication

Workout Agent uses Firebase Auth (Google Sign-In + email/password) to identify users. Set it up once:

1. Open https://console.firebase.google.com/ and select your GCP project (or click "Add project" and pick the same project ID).
2. In the left nav, go to **Build → Authentication → Get started**.
3. Enable the **Google** sign-in provider (set a support email).
4. Enable the **Email/Password** sign-in provider.
5. Go to **Project settings → General → Your apps**, click **Add app → Web** (the `</>` icon). Register a web app (any nickname). Firebase will show you a config snippet:
   ```js
   const firebaseConfig = {
     apiKey: "AIza...",
     authDomain: "your-project.firebaseapp.com",
     projectId: "your-project",
     ...
   };
   ```
   You'll need the `apiKey` and `authDomain` values in the next step. The `apiKey` is **public** by design — it's safe to ship to the browser.

### Generate an encryption key

This server-side key encrypts every user's Hevy API key before it's stored in Firestore:

```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

Keep the output safe (e.g. in your password manager). If you lose it, all stored API keys become unrecoverable.

## 2. Configure Terraform

```bash
cd infra
cp terraform.tfvars.example terraform.tfvars
```

Edit `terraform.tfvars`:

```hcl
project_id           = "my-gcp-project-123"
region               = "europe-west1"
firestore_location   = "eur3"
encryption_key       = "PASTE-GENERATED-FERNET-KEY-HERE"
firebase_api_key     = "AIza..."
firebase_auth_domain = "my-gcp-project-123.firebaseapp.com"
gemini_model         = "gemini-3-flash"
```

Common Firestore locations: `eur3` (multi-region EU), `nam5` (multi-region US), or any single region like `europe-west1`.

## 3. Provision infrastructure

```bash
cd infra
terraform init
terraform apply
```

Terraform will:

1. Enable required APIs (Vertex AI, Cloud Run, Cloud Build, Artifact Registry, Firebase, Identity Toolkit, Firestore).
2. Create a least-privilege service account with access to Vertex AI, Firestore, and Firebase Auth.
3. Create a Firestore database in native mode.
4. Apply restrictive Firestore security rules (no client-side access; the backend uses the Admin SDK).
5. Create an Artifact Registry Docker repository.
6. Create a public Cloud Run service (the app authenticates users itself via Firebase Auth).

> If a Firestore database already exists in your project, import it first:
> ```bash
> terraform import google_firestore_database.default "projects/PROJECT_ID/databases/(default)"
> ```

## 4. Build and deploy

From the repo root:

```bash
./deploy.sh
```

This script builds the Docker image via Cloud Build and rolls out a new Cloud Run revision. When it finishes, it prints the live service URL.

## 5. Updating the app

After code changes, just re-run `./deploy.sh`. You only need to re-run `terraform apply` if you've changed infrastructure (env vars, IAM, etc.).

## 6. Tearing down

```bash
cd infra
terraform destroy
```

This removes Cloud Run, the service account, IAM bindings, the Artifact Registry repository, and the Firestore database. **All user data in Firestore will be lost.** APIs stay enabled (Terraform doesn't disable them to avoid breaking other things in the project).

## 7. Importing existing resources

If you've already deployed the previous single-user version, you'll want to import existing resources into the new Terraform layout:

```bash
cd infra
terraform init

# API enablements (only the new ones — existing apis are unchanged)
for api in firebase identitytoolkit firestore; do
  terraform import "google_project_service.apis[\"$api.googleapis.com\"]" PROJECT_ID/$api.googleapis.com
done

# Firestore (if already exists)
terraform import google_firestore_database.default "projects/PROJECT_ID/databases/(default)"

# Service account + existing IAM bindings (already imported from v0.1)
```

Replace `PROJECT_ID` with your project ID.

## Local development

1. Create a `.env` file in the project root:

   ```
   GOOGLE_CLOUD_PROJECT=your-project-id
   GOOGLE_CLOUD_LOCATION=europe-west1
   GEMINI_MODEL=gemini-3-flash
   FIREBASE_PROJECT_ID=your-project-id
   FIREBASE_API_KEY=AIza...
   FIREBASE_AUTH_DOMAIN=your-project-id.firebaseapp.com
   ENCRYPTION_KEY=PASTE-GENERATED-FERNET-KEY-HERE
   ```

2. Install Python dependencies (requires [`uv`](https://docs.astral.sh/uv/)):

   ```bash
   uv venv && source .venv/bin/activate
   uv pip install -e .
   ```

3. Make sure Node.js is installed (needed for the `hevy-mcp` subprocess).

4. Make sure your shell has Application Default Credentials available:

   ```bash
   gcloud auth application-default login
   ```

5. Run the dev server:

   ```bash
   uv run uvicorn app.main:app --host 0.0.0.0 --port 8080 --reload
   ```

6. Open http://localhost:8080.

> Your local environment needs IAM permissions on Firestore and Firebase Auth Admin for the backend. The easiest way is to add the `roles/datastore.user` and `roles/firebaseauth.admin` roles to your own user account on the project for development.
