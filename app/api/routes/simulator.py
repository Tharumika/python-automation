from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_db
from app.schemas.workflow_runs import EventIngestResponse
from app.services.events import IngestionConflictError, ingest_event_payload
from app.services.simulator import SCENARIOS, build_simulated_event

router = APIRouter(prefix="/simulator", tags=["simulator"])


@router.get("/scenarios")
def list_scenarios() -> dict[str, list[str]]:
    return {"scenarios": list(SCENARIOS)}


@router.post("/events/{scenario}", response_model=EventIngestResponse, status_code=status.HTTP_202_ACCEPTED)
def simulate_event(
    scenario: str,
    request: Request,
    db: Session = Depends(get_db),
) -> EventIngestResponse:
    try:
        headers, payload = build_simulated_event(
            scenario=scenario,
            project_id=request.app.state.settings.default_gcp_project_id,
        )
        return ingest_event_payload(
            db=db,
            headers={
                **headers,
                "x-api-key": next(iter(request.app.state.settings.ingest_api_keys), "dev-ingest-key"),
            },
            payload=payload,
            settings=request.app.state.settings,
        )
    except IngestionConflictError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except ValueError as exc:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(exc)) from exc
