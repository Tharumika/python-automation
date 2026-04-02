# Event-Driven Cloud Operations Automation Hub

## 1. Project Goal

Build a Python-based cloud operations automation platform that listens to cloud and operational events, evaluates rules, triggers automated workflows, and tracks execution results through an API and dashboard.

This project is designed to be strong for a cloud solutions and services job application because it demonstrates:

- event-driven architecture
- Python backend engineering
- cloud operations automation
- remediation workflows
- observability and auditability
- secure, production-minded design

## 2. Recommended Positioning For Your Portfolio

Use this as a **Google Cloud-first, cloud-native automation platform** with a design that can later support AWS or Azure connectors.

Why GCP-first:

- it fits your updated direction for the portfolio project
- Google Cloud has strong event-driven services such as Eventarc, Pub/Sub, Cloud Run, and Cloud Monitoring
- it gives the project a clean modern architecture while staying realistic to build

## 3. Problem Statement

Cloud teams receive events from many systems such as monitoring alerts, audit logs, infrastructure changes, failed deployments, and cost anomalies. Manual handling is slow, inconsistent, and hard to audit.

This project solves that by:

- ingesting events from cloud and internal systems
- normalizing them into a standard structure
- matching them against automation rules
- executing remediation or notification workflows
- tracking every action with logs, status, and retry history

## 4. High-Level Solution

The platform will have five core layers:

1. Event ingestion layer
- receives events from EventBridge webhooks, API calls, schedulers, or queue consumers

2. Normalization layer
- converts raw cloud/vendor events into a standard internal event schema

3. Rule engine
- decides what automation should run based on event type, severity, source, tags, and policy conditions

4. Workflow execution layer
- runs actions such as Slack alerts, email, ticket creation, Lambda invocation, EC2 action, or custom Python jobs

5. Audit and control layer
- stores event history, execution results, retries, failures, and manual approvals

## 5. MVP Scope

Start with a focused MVP that is realistic, interview-friendly, and expandable.

### MVP Use Cases

1. CloudWatch alarm event arrives
- normalize the event
- apply a matching automation rule
- send Slack or email alert
- record execution status

2. EC2 instance health failure event arrives
- check instance tags and policy
- trigger an approved remediation action such as restart or notify-only
- store full execution log

3. Unauthorized security change event arrives from CloudTrail
- classify severity
- create incident record
- send urgent notification

4. Scheduled housekeeping automation
- run daily checks for tagged resources
- detect policy drift
- generate summary report

## 6. Target Architecture

### Main Components

- `FastAPI` control plane for APIs, admin operations, health checks, and configuration
- `PostgreSQL` for events, rules, workflow runs, and audit history
- `Redis` or `AWS SQS` for async job processing
- `Celery` or custom worker service for background task execution
- `Pydantic` models for event schemas and validation
- `SQLAlchemy` for persistence
- `Docker` and `docker-compose` for local development
- `Terraform` for cloud infrastructure
- `Google Eventarc` or webhook gateway for cloud event ingestion
- `Slack/Email/Ticketing` connector layer for outbound actions

### Preferred Initial Deployment Pattern

- FastAPI app on Cloud Run
- PostgreSQL on Cloud SQL or local container for development
- Pub/Sub for queued workflow jobs
- Eventarc sending events to an API endpoint or queue

## 7. Core Modules

### A. Event Ingestion Service

Responsibilities:

- accept inbound events from API/webhooks
- validate signatures if needed
- enqueue accepted events
- reject malformed or unauthorized requests

Key features:

- `/events/ingest` endpoint
- authentication with API key or signed requests
- raw payload storage for auditability

### B. Event Normalizer

Responsibilities:

- map source-specific payloads into a common internal schema
- enrich events with severity, source, region, account, and tags

Example normalized event fields:

- `event_id`
- `source`
- `event_type`
- `severity`
- `account_id`
- `region`
- `resource_id`
- `resource_type`
- `timestamp`
- `raw_payload`
- `metadata`

### C. Rule Engine

Responsibilities:

- evaluate conditions against normalized events
- choose one or more workflows to execute
- support priority and enabled/disabled states

Example rule conditions:

- source equals `aws.cloudwatch`
- event type equals `alarm.triggered`
- severity in `high, critical`
- resource tag `auto_remediate=true`

### D. Workflow Engine

Responsibilities:

- execute actions in sequence
- support retries, timeouts, and failure handling
- support dry-run mode for safe demos

Workflow action examples:

- send Slack alert
- send email
- create incident ticket
- invoke AWS Lambda
- restart EC2 instance
- call a custom Python remediation plugin

### E. Dashboard and Admin API

Responsibilities:

- show events and workflow history
- expose rule management endpoints
- show execution metrics and recent failures

Good interview-ready endpoints:

- `GET /health`
- `POST /events/ingest`
- `GET /events`
- `GET /workflow-runs`
- `GET /rules`
- `POST /rules`
- `PATCH /rules/{id}`

## 8. Suggested Tech Stack

### Backend

- Python 3.12
- FastAPI
- Pydantic v2
- SQLAlchemy
- Alembic
- Celery or RQ
- boto3
- httpx

### Database and Messaging

- PostgreSQL
- Redis for local async development
- AWS SQS for cloud deployment

### DevOps and Infra

- Docker
- docker-compose
- Terraform
- GitHub Actions

### Testing

- pytest
- pytest-asyncio
- factory_boy
- coverage

## 9. Recommended Repository Structure

```text
cloud-ops-automation-hub/
  app/
    api/
    core/
    db/
    models/
    schemas/
    services/
      ingestion/
      normalization/
      rules/
      workflows/
      connectors/
    workers/
    utils/
    main.py
  tests/
    unit/
    integration/
  infra/
    terraform/
    docker/
  docs/
  scripts/
  .env.example
  docker-compose.yml
  requirements.txt
  README.md
```

## 10. Implementation Phases

### Phase 1. Foundation Setup

Deliverables:

- initialize project structure
- set up FastAPI app
- configure PostgreSQL and SQLAlchemy
- add Docker and environment management
- create health endpoint

Success criteria:

- app boots locally
- DB connection works
- basic CI lint/test pipeline runs

### Phase 2. Event Ingestion and Normalization

Deliverables:

- build `/events/ingest` endpoint
- define raw event and normalized event schemas
- store inbound events
- create normalizer interface and AWS event adapters

Success criteria:

- sample Cloud Monitoring and Cloud Audit Log payloads can be ingested and normalized

### Phase 3. Rule Engine

Deliverables:

- database models for rules
- condition evaluator
- rule matching service
- enable/disable and priority handling

Success criteria:

- one incoming event can trigger zero, one, or many workflows based on rules

### Phase 4. Workflow Execution

Deliverables:

- async job queue integration
- workflow runner
- retry and timeout support
- connector abstraction for Slack, email, and AWS actions

Success criteria:

- matched workflows execute and update run status in the database

### Phase 5. Dashboard and Visibility

Deliverables:

- event list endpoint
- workflow run history endpoint
- simple admin UI or templated dashboard
- metrics and structured logging

Success criteria:

- users can inspect what happened, when, and why

### Phase 6. Cloud Deployment and IaC

Deliverables:

- Terraform for core infrastructure
- deployment configuration
- queue, IAM roles, and secrets setup
- hosted demo environment

Success criteria:

- the platform runs in the cloud and handles real or simulated events

### Phase 7. Production Hardening

Deliverables:

- authentication and authorization
- request signature validation
- rate limiting
- dead-letter queue strategy
- audit trail improvements
- error budget and alerting

Success criteria:

- the project looks production-aware and enterprise-ready

## 11. First Milestone To Build

The best first milestone is:

**Milestone 1: Ingest, normalize, and store cloud events**

Scope:

- FastAPI project bootstrapped
- PostgreSQL models created
- `/events/ingest` endpoint working
- sample AWS event payloads accepted
- normalized event saved to database
- event list endpoint available

Why this is the right first step:

- it creates the backbone for every later feature
- it gives you a visible demo early
- it lets us test architecture before adding rules and automation actions

## 12. Data Model Draft

### Tables

`raw_events`
- id
- source
- payload
- received_at
- status

`normalized_events`
- id
- raw_event_id
- event_type
- severity
- account_id
- region
- resource_id
- resource_type
- occurred_at
- metadata

`rules`
- id
- name
- source_filter
- event_type_filter
- severity_filter
- conditions_json
- enabled
- priority

`workflow_runs`
- id
- normalized_event_id
- rule_id
- action_type
- status
- started_at
- finished_at
- result_payload
- error_message

## 13. Non-Functional Requirements

- idempotent event processing
- structured JSON logging
- retry-safe workflow execution
- secret management through environment variables or secret store
- auditability for every event and automation run
- modular connectors so new cloud services can be added easily

## 14. Security Design

- secure inbound event endpoints with API keys or request signatures
- store minimal secrets and never log credentials
- enforce least-privilege IAM for remediation actions
- support dry-run mode to prevent dangerous remediation during demos
- add approval gates for high-risk actions later

## 15. Testing Strategy

### Unit Tests

- event schema validation
- normalization mapping
- rule evaluation logic
- workflow action dispatching

### Integration Tests

- ingest endpoint to DB persistence
- queue to workflow execution
- connector mocks for Slack and AWS

### Demo Tests

- replay sample CloudWatch alarm event
- replay sample CloudTrail security event
- confirm workflow execution record appears in dashboard

## 16. What Will Make This Project Stand Out

- use a normalized event model instead of hardcoding one cloud source
- show real automation state tracking, not just alerts
- include dry-run mode and audit logging
- package it with Terraform and Docker so it looks deployment-ready
- include sample cloud event payloads in `docs/` or `tests/fixtures/`

## 17. Resume-Ready Description

Built a Python-based event-driven cloud operations automation platform using FastAPI, PostgreSQL, and AWS integrations to ingest cloud events, evaluate automation rules, trigger remediation workflows, and maintain auditable execution history for operational and security incidents.

## 18. Recommended Build Order

1. foundation and local environment
2. event ingestion API
3. normalization models and persistence
4. event listing and audit endpoints
5. rule engine
6. workflow runner
7. outbound connectors
8. cloud deployment with Terraform
9. observability and security hardening

## 19. Immediate Next Step

Start building the project skeleton with:

- FastAPI app
- config management
- database setup
- Docker files
- first event ingestion endpoint

That gives us a solid base to begin implementation cleanly.
