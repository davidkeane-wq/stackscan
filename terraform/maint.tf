terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }

  backend "gcs" {
    bucket = "stackscan-tfstate"
    prefix = "terraform/state"
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

resource "google_artifact_registry_repository" "app" {
  location      = var.region
  repository_id = "stackscan"
  format        = "DOCKER"
}

resource "google_storage_bucket" "tfstate" {
  name          = "stackscan-tfstate"
  location      = var.region
  force_destroy = false
  uniform_bucket_level_access = true

  versioning {
    enabled = true
  }
}

resource "google_storage_bucket" "scan_results" {
  name          = "stackscan-scan-results"
  location      = var.region
  force_destroy = false
  uniform_bucket_level_access = true
}
resource "google_cloud_run_v2_service" "app" {
  name     = "stackscan"
  location = var.region

  template {
    containers {
      image = "${var.region}-docker.pkg.dev/${var.project_id}/stackscan/stackscan-app:latest"

      ports {
        container_port = 8080
      }
      env {
        name  = "GITHUB_TOKEN"
        value = var.github_token
      }
      env {
        name  = "DASHBOARD_TOKEN"
        value = var.dashboard_token
      }
      env {
        name  = "DASHBOARD_URL"
        value = var.dashboard_url
      }
      env {
        name  = "SCAN_RESULTS_BUCKET"
        value = google_storage_bucket.scan_results.name
      }

      resources {
        limits = {
          cpu    = "1"
          memory = "512Mi"
        }
      }
    }

    scaling {
      min_instance_count = 0
      max_instance_count = 3
    }
  }
}

resource "google_cloud_run_v2_service_iam_member" "public" {
  project  = var.project_id
  location = var.region
  name     = google_cloud_run_v2_service.app.name
  role     = "roles/run.invoker"
  member   = "allUsers"
}

resource "google_storage_bucket_iam_member" "scan_results_admin" {
  bucket = google_storage_bucket.scan_results.name
  role   = "roles/storage.objectAdmin"
  member = "serviceAccount:${data.google_compute_default_service_account.default.email}"
}

data "google_compute_default_service_account" "default" {
  project = var.project_id
}