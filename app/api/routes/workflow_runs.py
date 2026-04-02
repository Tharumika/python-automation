from __future__ import annotations

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.orm import Session

from app.api.dependencies import get_db
from app.models import WorkflowRun
from app.schemas.workflow_runs import WorkflowRunRead

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
