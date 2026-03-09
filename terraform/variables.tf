variable "project_id" {
  description = "GCP project ID"
  type        = string
}

variable "region" {
  description = "GCP region"
  type        = string
  default     = "australia-southeast1"
}

variable "github_token" {
  description = "GitHub token for the app"
  type        = string
  sensitive   = true
}