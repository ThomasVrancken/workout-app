locals {
  image = "${var.region}-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.app.repository_id}/workout-agent:latest"
}

# ── Artifact Registry ───────────────────────────────────

resource "google_artifact_registry_repository" "app" {
  location      = var.region
  repository_id = "workout-agent"
  format        = "DOCKER"
  description   = "Docker images for the Workout Agent app"

  depends_on = [google_project_service.apis]
}

# ── Cloud Run service ───────────────────────────────────

resource "google_cloud_run_v2_service" "workout_agent" {
  name     = "workout-agent"
  location = var.region

  template {
    service_account = google_service_account.workout_agent.email

    containers {
      image = "gcr.io/cloudrun/hello" # placeholder; real image is pushed by deploy.sh

      ports {
        container_port = 8080
      }

      env {
        name  = "GOOGLE_CLOUD_PROJECT"
        value = var.project_id
      }
      env {
        name  = "GOOGLE_CLOUD_LOCATION"
        value = var.region
      }
      env {
        name  = "GEMINI_MODEL"
        value = var.gemini_model
      }
      env {
        name  = "FIREBASE_PROJECT_ID"
        value = var.project_id
      }
      env {
        name  = "FIREBASE_API_KEY"
        value = var.firebase_api_key
      }
      env {
        name  = "FIREBASE_AUTH_DOMAIN"
        value = var.firebase_auth_domain
      }
      env {
        name  = "ENCRYPTION_KEY"
        value = var.encryption_key
      }
    }
  }

  lifecycle {
    ignore_changes = [
      template[0].containers[0].image,
      client,
      client_version,
    ]
  }

  depends_on = [
    google_project_service.apis,
    google_firestore_database.default,
  ]
}

# Public access — the app gates everything behind Firebase Auth at the app layer.
resource "google_cloud_run_v2_service_iam_member" "public" {
  name     = google_cloud_run_v2_service.workout_agent.name
  location = var.region
  role     = "roles/run.invoker"
  member   = "allUsers"
}
