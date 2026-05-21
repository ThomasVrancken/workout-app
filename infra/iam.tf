resource "google_service_account" "workout_agent" {
  account_id   = "workout-agent-sa"
  display_name = "Workout Agent Cloud Run SA"

  depends_on = [google_project_service.apis]
}

# Required for Gemini via Vertex AI
resource "google_project_iam_member" "vertex_ai_user" {
  project = var.project_id
  role    = "roles/aiplatform.user"
  member  = "serviceAccount:${google_service_account.workout_agent.email}"
}

# Required for Firestore reads/writes (user docs)
resource "google_project_iam_member" "firestore_user" {
  project = var.project_id
  role    = "roles/datastore.user"
  member  = "serviceAccount:${google_service_account.workout_agent.email}"
}

# Required to verify Firebase ID tokens server-side
resource "google_project_iam_member" "firebase_auth_admin" {
  project = var.project_id
  role    = "roles/firebaseauth.admin"
  member  = "serviceAccount:${google_service_account.workout_agent.email}"
}
