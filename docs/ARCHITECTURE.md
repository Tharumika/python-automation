# Architecture Overview

## Intent

This project is designed as a GCP-first cloud operations automation backend that can receive events from multiple Google Cloud sources and make automation decisions in a consistent, auditable way.

## Event Sources

- `Eventarc` CloudEvents
- `Cloud Monitoring` alerts
- `Cloud Audit Logs`
- `Pub/Sub` push subscriptions
- generic GCP-originated webhooks

## Processing Flow

1. An event lands on `POST /api/v1/events/ingest`.
2. The raw payload and headers are stored in `raw_events`.
3. The GCP normalizer converts the payload into a standard internal event model.
4. The rule engine matches the normalized event against active rules.
5. The workflow dispatcher records an automation run for each matched rule.
6. Operators can review the full chain through the API.

## Current Safety Model

- ingestion requires `x-api-key`
- duplicate normalized events are blocked via `dedupe_key`
- workflows default to `dry_run=true`
- raw payloads and workflow results are retained for auditability

## Current GCP Mapping

- `Cloud Run` is the recommended hosting target
- `Cloud SQL PostgreSQL` is the recommended managed database
- `Eventarc` is the recommended event routing layer
- `Pub/Sub` is the recommended queue backbone for future async workers

## Expansion Path

- replace dry-run connectors with real Slack, email, Jira, or PagerDuty integrations
- add service account authentication and request validation
- offload workflow execution to background workers
- add approval gates for destructive remediations
- introduce Terraform modules per environment
