from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy.orm import Session, joinedload

from app.core.config import Settings
from app.models import NormalizedEvent, Rule, WorkflowRun, WorkflowTask
from app.services.connectors.notifications import NotificationConnector


def enqueue_workflows(
    db: Session,
    event: NormalizedEvent,
    rules: list[Rule],
    settings: Settings,
) -> list[WorkflowRun]:
    workflow_runs: list[WorkflowRun] = []

    for rule in rules:
        workflow_run = WorkflowRun(
            normalized_event_id=event.id,
            rule_id=rule.id,
            action_type=rule.action_type,
            status="queued",
            dry_run=settings.dry_run,
            result_payload={"queue_state": "waiting"},
        )
        db.add(workflow_run)
        db.flush()

        workflow_task = WorkflowTask(
            workflow_run_id=workflow_run.id,
            status="queued",
        )
        db.add(workflow_task)
        db.flush()
        workflow_runs.append(workflow_run)

    return workflow_runs


def process_workflow_queue(
    db: Session,
    settings: Settings,
    limit: int | None = None,
    workflow_run_ids: list[str] | None = None,
) -> list[WorkflowRun]:
    batch_limit = limit or settings.workflow_queue_batch_size
    connector = NotificationConnector(timeout_seconds=settings.webhook_timeout_seconds)

    query = (
        db.query(WorkflowTask)
        .options(
            joinedload(WorkflowTask.workflow_run).joinedload(WorkflowRun.normalized_event),
            joinedload(WorkflowTask.workflow_run).joinedload(WorkflowRun.rule),
        )
        .filter(WorkflowTask.status == "queued")
        .order_by(WorkflowTask.scheduled_at.asc())
    )

    if workflow_run_ids:
        query = query.filter(WorkflowTask.workflow_run_id.in_(workflow_run_ids))

    tasks = query.limit(batch_limit).all()
    processed_runs: list[WorkflowRun] = []

    for task in tasks:
        workflow_run = task.workflow_run
        if workflow_run is None or workflow_run.normalized_event is None or workflow_run.rule is None:
            continue

        task.status = "running"
        task.attempt_count += 1
        task.started_at = datetime.now(UTC)
        workflow_run.status = "running"
        workflow_run.started_at = datetime.now(UTC)
        db.add(task)
        db.add(workflow_run)
        db.flush()

        try:
            result_payload = dispatch_rule_action(
                rule=workflow_run.rule,
                event=workflow_run.normalized_event,
                settings=settings,
                connector=connector,
            )
            workflow_run.status = "simulated" if settings.dry_run else "completed"
            workflow_run.result_payload = result_payload
            workflow_run.error_message = None
            workflow_run.finished_at = datetime.now(UTC)
            task.status = "completed"
            task.last_error = None
            task.finished_at = datetime.now(UTC)
        except Exception as exc:
            workflow_run.status = "failed"
            workflow_run.result_payload = {}
            workflow_run.error_message = str(exc)
            workflow_run.finished_at = datetime.now(UTC)
            task.status = "failed"
            task.last_error = str(exc)
            task.finished_at = datetime.now(UTC)

        db.add(task)
        db.add(workflow_run)
        db.flush()
        processed_runs.append(workflow_run)

    return processed_runs


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
