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

variable "dashboard_token" {
  description = "Bearer token used to authenticate POST requests to the dashboard scan API"
  type        = string
  sensitive   = true
}

variable "dashboard_url" {
  description = "Public base URL of the deployed dashboard (e.g. https://stackscan-xxx-ts.a.run.app)"
  type        = string
  default     = ""
}