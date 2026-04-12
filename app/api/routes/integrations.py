from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.api.dependencies import get_db
from app.schemas.integrations import IntegrationStatusResponse, IntegrationTestResponse
from app.services.integrations import get_integration_status, run_integration_test

router = APIRouter(prefix="/integrations", tags=["integrations"])


@router.get("/status", response_model=IntegrationStatusResponse)
def integration_status(request: Request) -> IntegrationStatusResponse:
    return get_integration_status(request.app.state.settings)


@router.post("/test/notify", response_model=IntegrationTestResponse)
def test_notify_integration(
    request: Request,
    db: Session = Depends(get_db),
) -> IntegrationTestResponse:
    try:
        return run_integration_test(
            db=db,
            settings=request.app.state.settings,
            test_type="notify",
        )
    except ValueError as exc:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/test/incident", response_model=IntegrationTestResponse)
def test_incident_integration(
    request: Request,
    db: Session = Depends(get_db),
) -> IntegrationTestResponse:
    try:
        return run_integration_test(
            db=db,
            settings=request.app.state.settings,
            test_type="incident",
        )
    except ValueError as exc:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(exc)) from exc
