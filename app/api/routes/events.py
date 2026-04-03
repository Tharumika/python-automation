from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_db
from app.models import NormalizedEvent, RawEvent
from app.schemas.events import NormalizedEventDetailRead, NormalizedEventRead, RawEventRead
from app.schemas.workflow_runs import EventIngestResponse
from app.services.events import (
    IngestionAuthenticationError,
    IngestionConflictError,
    ingest_event_payload,
)

router = APIRouter(prefix="/events", tags=["events"])


@router.post("/ingest", response_model=EventIngestResponse, status_code=status.HTTP_202_ACCEPTED)
async def ingest_event(request: Request, db: Session = Depends(get_db)) -> EventIngestResponse:
    try:
        payload = await request.json()
    except Exception as exc:  # pragma: no cover - FastAPI wraps request parsing differently in prod.
        raise HTTPException(status_code=400, detail="Request body must be valid JSON.") from exc

    try:
        return ingest_event_payload(
            db=db,
            headers=dict(request.headers),
            payload=payload,
            settings=request.app.state.settings,
        )
    except IngestionAuthenticationError as exc:
        db.rollback()
        raise HTTPException(status_code=401, detail=str(exc)) from exc
    except IngestionConflictError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except ValueError as exc:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/raw", response_model=list[RawEventRead])
def list_raw_events(
    limit: int = Query(default=50, ge=1, le=200),
    db: Session = Depends(get_db),
) -> list[RawEventRead]:
    return db.query(RawEvent).order_by(RawEvent.received_at.desc()).limit(limit).all()


@router.get("/normalized", response_model=list[NormalizedEventRead])
def list_normalized_events(
    limit: int = Query(default=50, ge=1, le=200),
    db: Session = Depends(get_db),
) -> list[NormalizedEventRead]:
    return (
        db.query(NormalizedEvent)
        .order_by(NormalizedEvent.occurred_at.desc())
        .limit(limit)
        .all()
    )


@router.get("/normalized/{event_id}", response_model=NormalizedEventDetailRead)
def get_normalized_event(
    event_id: str,
    db: Session = Depends(get_db),
) -> NormalizedEventDetailRead:
    event = db.query(NormalizedEvent).filter(NormalizedEvent.id == event_id).one_or_none()
    if event is None:
        raise HTTPException(status_code=404, detail="Normalized event not found.")
    return event
