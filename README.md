# GCP Cloud Ops Automation Hub

GCP Cloud Ops Automation Hub is a Python-based event-driven automation platform for cloud operations teams. It ingests Google Cloud events, normalizes them into a standard schema, evaluates rules, and records automation workflows with a clear audit trail.

This repository is intentionally shaped as a portfolio-grade cloud solutions project:

- `FastAPI` control plane
- `SQLAlchemy` persistence layer
- GCP-first event normalization for Eventarc, Cloud Audit Logs, Cloud Monitoring, and Pub/Sub push
- rule engine with seeded operational workflows
- workflow execution logging for safe dry-run demos
- Docker and Terraform scaffolding for local development and GCP deployment

## MVP Capabilities

- accept GCP CloudEvents through `POST /api/v1/events/ingest`
- normalize monitoring alerts, audit log events, and Pub/Sub push events
- deduplicate normalized events with a SHA-256 event fingerprint
- evaluate seeded or custom automation rules
- record workflow runs for notifications and incident creation
- inspect raw events, normalized events, rules, and workflow runs through API endpoints

## Architecture

### Local runtime

- `FastAPI` for the API surface
- `SQLite` by default for zero-friction startup
- `PostgreSQL` via Docker Compose for a production-like local environment

### GCP deployment path

- `Cloud Run` for the API service
- `Cloud SQL for PostgreSQL` for persistence
- `Eventarc` to route Google Cloud events
- `Pub/Sub` for async event sources and future worker expansion

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for the design overview.

## Quick Start

1. Create a virtual environment and install dependencies.

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

2. Copy the environment template.

```powershell
Copy-Item .env.example .env
```

3. Run the API.

```powershell
uvicorn app.main:app --reload
```

4. Open the interactive docs.

- [Swagger UI](http://127.0.0.1:8000/docs)

## Docker Compose

```powershell
docker compose up --build
```

The Compose stack starts:

- `api` on port `8000`
- `postgres` on port `5432`

## Sample Event Ingestion

```powershell
$headers = @{
  "Content-Type" = "application/json"
  "x-api-key" = "dev-ingest-key"
  "ce-id" = "evt-monitoring-001"
  "ce-type" = "google.cloud.monitoring.alert.v1.opened"
  "ce-source" = "//monitoring.googleapis.com/projects/demo-project/alerts/alert-1"
  "ce-time" = "2026-04-02T16:05:00Z"
}

$body = @"
{
  "data": {
    "incident": {
      "state": "open",
      "summary": "High CPU usage detected"
    },
    "resource": {
      "type": "gce_instance",
      "labels": {
        "project_id": "demo-project",
        "instance_id": "1234567890",
        "location": "us-central1-a"
      }
    }
  }
}
"@

Invoke-RestMethod -Method Post -Uri "http://127.0.0.1:8000/api/v1/events/ingest" -Headers $headers -Body $body
```

## Main Endpoints

- `GET /health`
- `POST /api/v1/events/ingest`
- `GET /api/v1/events/raw`
- `GET /api/v1/events/normalized`
- `GET /api/v1/rules`
- `POST /api/v1/rules`
- `PATCH /api/v1/rules/{rule_id}`
- `GET /api/v1/workflow-runs`

## Tests

```powershell
pytest
```

## Suggested Next Enhancements

- add signed request validation for Eventarc or API Gateway
- push workflow execution into Pub/Sub or Cloud Tasks
- add Cloud Logging and Monitoring exporters
- add a lightweight admin UI
- add Cloud Build or GitHub Actions deployment automation
