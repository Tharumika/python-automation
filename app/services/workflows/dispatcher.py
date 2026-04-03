from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.core.config import Settings
from app.models import NormalizedEvent, Rule, WorkflowRun
from app.services.connectors.notifications import NotificationConnector


def execute_workflows(
    db: Session,
    event: NormalizedEvent,
    rules: list[Rule],
    settings: Settings,
) -> list[WorkflowRun]:
    connector = NotificationConnector(timeout_seconds=settings.webhook_timeout_seconds)
    workflow_runs: list[WorkflowRun] = []

    for rule in rules:
        started_at = datetime.now(UTC)
        try:
            result_payload = dispatch_rule_action(rule, event, settings, connector)
            status = "simulated" if settings.dry_run else "completed"
            workflow_run = WorkflowRun(
                normalized_event_id=event.id,
                rule_id=rule.id,
                action_type=rule.action_type,
                status=status,
                dry_run=settings.dry_run,
                result_payload=result_payload,
                started_at=started_at,
                finished_at=datetime.now(UTC),
            )
        except Exception as exc:
            workflow_run = WorkflowRun(
                normalized_event_id=event.id,
                rule_id=rule.id,
                action_type=rule.action_type,
                status="failed",
                dry_run=settings.dry_run,
                result_payload={},
                error_message=str(exc),
                started_at=started_at,
                finished_at=datetime.now(UTC),
            )

        db.add(workflow_run)
        db.flush()
        workflow_runs.append(workflow_run)

    return workflow_runs


def dispatch_rule_action(
    rule: Rule,
    event: NormalizedEvent,
    settings: Settings,
    connector: NotificationConnector,
) -> dict:
    summary = (
        f"{event.severity.upper()} {event.event_type} for project={event.project_id} "
        f"resource={event.resource_id or 'n/a'}"
    )

    if rule.action_type == "notify":
        return connector.send(
            target=rule.action_target or "platform-ops",
            subject=f"[{event.severity.upper()}] Cloud automation event",
            message=summary,
            dry_run=settings.dry_run,
            webhook_url=settings.notification_webhook_url,
        )

    if rule.action_type == "create_incident":
        return connector.create_incident(
            queue=rule.action_target or "security-response",
            title=f"Investigate {event.event_type}",
            description=summary,
            dry_run=settings.dry_run,
            webhook_url=settings.incident_webhook_url,
        )

    return {
        "delivery": "skipped",
        "reason": f"Unsupported action type '{rule.action_type}'.",
    }
