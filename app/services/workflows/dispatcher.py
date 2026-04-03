from __future__ import annotations

from sqlalchemy.orm import Session

from app.core.config import Settings
from app.models import NormalizedEvent, Rule, WorkflowRun
from app.services.workflows.queue import enqueue_workflows, process_workflow_queue


def execute_workflows(
    db: Session,
    event: NormalizedEvent,
    rules: list[Rule],
    settings: Settings,
) -> list[WorkflowRun]:
    workflow_runs = enqueue_workflows(db, event, rules, settings)
    if settings.auto_process_workflow_queue and workflow_runs:
        process_workflow_queue(
            db=db,
            settings=settings,
            workflow_run_ids=[workflow_run.id for workflow_run in workflow_runs],
        )
        for workflow_run in workflow_runs:
            db.refresh(workflow_run)
    return workflow_runs
