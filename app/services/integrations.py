from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy.orm import Session

from app.core.config import Settings
from app.models import NormalizedEvent, RawEvent, Rule, WorkflowRun
from app.schemas.integrations import IntegrationStatusResponse, IntegrationTestResponse
from app.services.workflows.queue import enqueue_workflows, process_workflow_queue


TEST_RULE_CONFIG = {
    "notify": {
        "name": "[System] Integration test notification",
        "description": "System-generated rule used for safe notification integration tests.",
        "action_type": "notify",
        "action_target": "integration-test",
        "severity_filter": "info",
        "priority": 999,
    },
    "incident": {
        "name": "[System] Integration test incident",
        "description": "System-generated rule used for safe incident integration tests.",
        "action_type": "create_incident",
        "action_target": "integration-test",
        "severity_filter": "high",
        "priority": 999,
    },
}


def get_integration_status(settings: Settings) -> IntegrationStatusResponse:
    return IntegrationStatusResponse(
        mode="dry-run" if settings.dry_run else "live",
        dry_run=settings.dry_run,
        slack_configured=bool(settings.slack_webhook_url),
        slack_destination_label=settings.slack_destination_label,
        notification_webhook_configured=bool(settings.notification_webhook_url),
        incident_webhook_configured=bool(settings.incident_webhook_url),
    )


def run_integration_test(
    db: Session,
    settings: Settings,
    test_type: str,
) -> IntegrationTestResponse:
    if test_type not in TEST_RULE_CONFIG:
        raise ValueError(f"Unsupported integration test type '{test_type}'.")

    raw_event = _create_test_raw_event(db=db, test_type=test_type)
    normalized_event = _create_test_normalized_event(
        db=db,
        raw_event=raw_event,
        settings=settings,
        test_type=test_type,
    )
    rule = _get_or_create_test_rule(db=db, test_type=test_type)

    workflow_runs = enqueue_workflows(
        db=db,
        event=normalized_event,
        rules=[rule],
        settings=settings,
    )
    processed_runs = process_workflow_queue(
        db=db,
        settings=settings,
        workflow_run_ids=[workflow_run.id for workflow_run in workflow_runs],
        limit=1,
    )

    raw_event.status = "processed"
    db.add(raw_event)
    db.commit()

    workflow_run = processed_runs[0]
    db.refresh(workflow_run)

    return IntegrationTestResponse(
        test_type=test_type,
        queue_processed=True,
        workflow_run_id=workflow_run.id,
        workflow_status=workflow_run.status,
        delivery=str(workflow_run.result_payload.get("delivery", "unknown")),
        connector_type=str(workflow_run.result_payload.get("connector_type", "unknown")),
        destination_label=str(workflow_run.result_payload.get("destination_label", "unknown")),
    )


def _create_test_raw_event(db: Session, test_type: str) -> RawEvent:
    timestamp = datetime.now(UTC).isoformat()
    raw_event = RawEvent(
        provider="gcp",
        source="system.integration-test",
        event_type=f"system.integration-test.{test_type}",
        headers_json={"x-source": "integration-test"},
        payload_json={
            "test_traffic": True,
            "test_type": test_type,
            "created_at": timestamp,
        },
        status="received",
    )
    db.add(raw_event)
    db.flush()
    return raw_event


def _create_test_normalized_event(
    db: Session,
    raw_event: RawEvent,
    settings: Settings,
    test_type: str,
) -> NormalizedEvent:
    now = datetime.now(UTC)
    normalized_event = NormalizedEvent(
        raw_event_id=raw_event.id,
        source="system.integration-test",
        event_type=f"system.integration-test.{test_type}",
        severity="high" if test_type == "incident" else "info",
        project_id=settings.default_gcp_project_id,
        region="global",
        resource_id=f"integration-test-{uuid4().hex[:10]}",
        resource_type="integration_test",
        dedupe_key=f"integration-test-{test_type}-{uuid4().hex}",
        occurred_at=now,
        metadata_json={
            "test_traffic": True,
            "integration_test_type": test_type,
            "test_label": "demo-safe-test-send",
            "created_at": now.isoformat(),
        },
    )
    db.add(normalized_event)
    db.flush()
    return normalized_event


def _get_or_create_test_rule(db: Session, test_type: str) -> Rule:
    config = TEST_RULE_CONFIG[test_type]
    existing = db.query(Rule).filter(Rule.name == config["name"]).one_or_none()
    if existing is not None:
        return existing

    rule = Rule(
        name=config["name"],
        description=config["description"],
        action_type=config["action_type"],
        action_target=config["action_target"],
        severity_filter=config["severity_filter"],
        priority=config["priority"],
        enabled=False,
    )
    db.add(rule)
    db.flush()
    return rule
