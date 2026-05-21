variable "project_id" {
  description = "GCP project ID"
  type        = string
}

variable "region" {
  description = "GCP region for Cloud Run and Artifact Registry"
  type        = string
  default     = "europe-west1"
}

variable "firestore_location" {
  description = "Firestore database location (must be a multi-region or region — see https://cloud.google.com/firestore/docs/locations)"
  type        = string
  default     = "eur3"
}

variable "encryption_key" {
  description = "Fernet key used to encrypt per-user Hevy API keys at rest. Generate with: python -c 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())'"
  type        = string
  sensitive   = true
}

variable "firebase_api_key" {
  description = "Firebase Web API key (public, used by the frontend). Find it in the Firebase Console → Project Settings → General → Your apps → Web app."
  type        = string
}

variable "firebase_auth_domain" {
  description = "Firebase Auth domain (e.g. PROJECT_ID.firebaseapp.com)"
  type        = string
}

variable "gemini_model" {
  description = "Gemini model name to use via Vertex AI"
  type        = string
  default     = "gemini-2.5-pro"
}
