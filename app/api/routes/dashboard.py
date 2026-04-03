from __future__ import annotations

from collections import Counter
from pathlib import Path

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.api.dependencies import get_db
from app.models import NormalizedEvent, RawEvent, Rule, WorkflowRun, WorkflowTask
from app.schemas.dashboard import DashboardSummaryResponse

templates = Jinja2Templates(directory=str(Path(__file__).resolve().parents[2] / "templates"))

router = APIRouter(tags=["dashboard"])


@router.get("/", response_class=HTMLResponse, include_in_schema=False)
def dashboard_page(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(
        request=request,
        name="dashboard.html",
        context={
            "app_name": request.app.state.settings.app_name,
            "api_prefix": request.app.state.settings.api_prefix,
        },
    )


@router.get("/dashboard/summary", response_model=DashboardSummaryResponse, include_in_schema=False)
def dashboard_summary(
    request: Request,
    db: Session = Depends(get_db),
) -> DashboardSummaryResponse:
    normalized_events = (
        db.query(NormalizedEvent)
        .order_by(NormalizedEvent.occurred_at.desc())
        .limit(8)
        .all()
    )
    workflow_runs = (
        db.query(WorkflowRun)
        .order_by(WorkflowRun.started_at.desc())
        .limit(8)
        .all()
    )
    rules = db.query(Rule).order_by(Rule.priority.asc(), Rule.created_at.asc()).all()

    severity_counter = Counter(event.severity for event in normalized_events)
    workflow_counter = Counter(run.status for run in workflow_runs)
    queue_counter = Counter(
        status
        for (status,) in db.query(WorkflowTask.status).all()
    )

    return DashboardSummaryResponse(
        headline="Live view of event ingestion, rule matching, and workflow execution.",
        processing_mode=(
            "auto-processing queue"
            if request.app.state.settings.auto_process_workflow_queue
            else "manual queue processing"
        ),
        total_raw_events=db.query(RawEvent).count(),
        total_normalized_events=db.query(NormalizedEvent).count(),
        enabled_rules=sum(1 for rule in rules if rule.enabled),
        total_rules=len(rules),
        total_workflow_runs=db.query(WorkflowRun).count(),
        queue_depth=queue_counter.get("queued", 0),
        severity_breakdown={
            key: severity_counter.get(key, 0)
            for key in ("critical", "high", "medium", "info")
        },
        workflow_breakdown={
            key: workflow_counter.get(key, 0)
            for key in ("queued", "running", "simulated", "completed", "failed")
        },
        queue_breakdown={
            key: queue_counter.get(key, 0)
            for key in ("queued", "running", "completed", "failed")
        },
        recent_events=[
            {
                "id": event.id,
                "event_type": event.event_type,
                "severity": event.severity,
                "project_id": event.project_id,
                "resource_type": event.resource_type,
                "resource_id": event.resource_id,
                "occurred_at": event.occurred_at,
                "source": event.source,
            }
            for event in normalized_events
        ],
        recent_workflow_runs=[
            {
                "id": run.id,
                "action_type": run.action_type,
                "status": run.status,
                "dry_run": run.dry_run,
                "started_at": run.started_at,
                "finished_at": run.finished_at,
                "rule_id": run.rule_id,
            }
            for run in workflow_runs
        ],
        rules=[
            {
                "id": rule.id,
                "name": rule.name,
                "description": rule.description,
                "enabled": rule.enabled,
                "priority": rule.priority,
                "action_type": rule.action_type,
                "action_target": rule.action_target,
                "severity_filter": rule.severity_filter,
                "event_type_filter": rule.event_type_filter,
            }
            for rule in rules
        ],
    )
