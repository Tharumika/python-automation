terraform {
  required_version = ">= 1.6.0"

  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.30"
    }
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

variable "project_id" {
  description = "Google Cloud project ID."
  type        = string
}

variable "region" {
  description = "Deployment region."
  type        = string
  default     = "us-central1"
}

variable "service_name" {
  description = "Cloud Run service name."
  type        = string
  default     = "gcp-cloud-ops-automation-hub"
}

variable "container_image" {
  description = "Container image for the API service."
  type        = string
}

resource "google_artifact_registry_repository" "api" {
  location      = var.region
  repository_id = "cloud-ops-automation"
  description   = "Artifact Registry for the cloud ops automation hub."
  format        = "DOCKER"
}

resource "google_pubsub_topic" "events" {
  name = "cloud-ops-events"
}

resource "google_pubsub_topic" "workflow_runs" {
  name = "cloud-ops-workflow-runs"
}

resource "google_cloud_run_v2_service" "api" {
  name     = var.service_name
  location = var.region
  ingress  = "INGRESS_TRAFFIC_ALL"

  template {
    service_account = null

    containers {
      image = var.container_image

      ports {
        container_port = 8000
      }

      env {
        name  = "ENVIRONMENT"
        value = "production"
      }

      env {
        name  = "DEFAULT_GCP_PROJECT_ID"
        value = var.project_id
      }

      env {
        name  = "DRY_RUN"
        value = "false"
      }
    }
  }
}

output "cloud_run_service_uri" {
  value = google_cloud_run_v2_service.api.uri
}
