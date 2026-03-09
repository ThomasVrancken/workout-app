resource "google_service_account" "workout_agent" {
  account_id   = "workout-agent-sa"
  display_name = "Workout Agent Cloud Run SA"

  depends_on = [google_project_service.apis]
}

resource "google_project_iam_member" "vertex_ai_user" {
  project = var.project_id
  role    = "roles/aiplatform.user"
  member  = "serviceAccount:${google_service_account.workout_agent.email}"
}
