output "service_url" {
  description = "Public URL of the deployed Workout Agent"
  value       = google_cloud_run_v2_service.workout_agent.uri
}

output "project_id" {
  description = "GCP project ID (used by deploy.sh)"
  value       = var.project_id
}

output "region" {
  description = "GCP region (used by deploy.sh)"
  value       = var.region
}

output "image" {
  description = "Full Artifact Registry image path (used by deploy.sh)"
  value       = local.image
}
