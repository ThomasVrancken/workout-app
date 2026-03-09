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
      # Placeholder for initial creation. The actual image is managed
      # by deploy.sh and ignored by Terraform after first apply.
      image = "gcr.io/cloudrun/hello"

      ports {
        container_port = 8080
      }

      env {
        name  = "HEVY_API_KEY"
        value = var.hevy_api_key
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
        name  = "APP_SECRET"
        value = var.app_secret
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

  depends_on = [google_project_service.apis]
}

# Allow unauthenticated access (app handles auth internally)
resource "google_cloud_run_v2_service_iam_member" "public" {
  name     = google_cloud_run_v2_service.workout_agent.name
  location = var.region
  role     = "roles/run.invoker"
  member   = "allUsers"
}
