variable "project_id" {
  description = "GCP project ID"
  type        = string
}

variable "region" {
  description = "GCP region for all resources"
  type        = string
  default     = "europe-west1"
}

variable "hevy_api_key" {
  description = "Hevy API key (https://api.hevyapp.com/account/api)"
  type        = string
  sensitive   = true
}

variable "app_secret" {
  description = "Shared passphrase for the chat UI login screen"
  type        = string
  sensitive   = true
}

variable "gemini_model" {
  description = "Gemini model name to use via Vertex AI"
  type        = string
  default     = "gemini-3-flash"
}
