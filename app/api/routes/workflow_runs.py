from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session

from app.api.dependencies import get_db
from app.models import WorkflowRun, WorkflowTask
from app.schemas.workflow_runs import (
    WorkflowQueueProcessResponse,
    WorkflowRunDetailRead,
    WorkflowRunRead,
)
from app.services.workflows.queue import process_workflow_queue

router = APIRouter(prefix="/workflow-runs", tags=["workflow-runs"])


@router.get("", response_model=list[WorkflowRunRead])
def list_workflow_runs(
    limit: int = Query(default=100, ge=1, le=200),
    db: Session = Depends(get_db),
) -> list[WorkflowRunRead]:
    return (
        db.query(WorkflowRun)
        .order_by(WorkflowRun.started_at.desc())
        .limit(limit)
        .all()
    )


@router.get("/queue/summary")
def workflow_queue_summary(
    db: Session = Depends(get_db),
) -> dict[str, int]:
    return {
        "queued": db.query(WorkflowTask).filter(WorkflowTask.status == "queued").count(),
        "running": db.query(WorkflowTask).filter(WorkflowTask.status == "running").count(),
        "failed": db.query(WorkflowTask).filter(WorkflowTask.status == "failed").count(),
        "completed": db.query(WorkflowTask).filter(WorkflowTask.status == "completed").count(),
    }


@router.post("/process-queue", response_model=WorkflowQueueProcessResponse)
def process_queue(
    request: Request,
    limit: int = Query(default=20, ge=1, le=200),
    db: Session = Depends(get_db),
) -> WorkflowQueueProcessResponse:
    processed_runs = process_workflow_queue(
        db=db,
        settings=request.app.state.settings,
        limit=limit,
    )
    db.commit()
    return WorkflowQueueProcessResponse(
        processed_count=len(processed_runs),
        processed_workflow_run_ids=[workflow_run.id for workflow_run in processed_runs],
    )


@router.get("/{workflow_run_id}", response_model=WorkflowRunDetailRead)
def get_workflow_run(
    workflow_run_id: str,
    db: Session = Depends(get_db),
) -> WorkflowRunDetailRead:
    workflow_run = db.query(WorkflowRun).filter(WorkflowRun.id == workflow_run_id).one_or_none()
    if workflow_run is None:
        raise HTTPException(status_code=404, detail="Workflow run not found.")
    return workflow_run
