from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from app.core.config import Settings
from app.models import NormalizedEvent, RawEvent
from app.schemas.workflow_runs import EventIngestResponse
from app.services.normalizers.gcp import normalize_gcp_event, peek_identity
from app.services.rules.engine import get_matching_rules
from app.services.workflows.dispatcher import execute_workflows


class IngestionAuthenticationError(Exception):
    """Raised when the ingest request cannot be authenticated."""


class IngestionConflictError(Exception):
    """Raised when an idempotent event already exists."""


def ingest_event_payload(
    db: Session,
    headers: dict[str, str],
    payload: dict[str, Any],
    settings: Settings,
) -> EventIngestResponse:
    api_key = headers.get("x-api-key")
    if settings.ingest_api_keys and api_key not in settings.ingest_api_keys:
        raise IngestionAuthenticationError("Invalid ingest API key.")

    source_hint, event_type_hint = peek_identity(headers, payload)
    raw_event = RawEvent(
        provider="gcp",
        source=source_hint,
        event_type=event_type_hint,
        headers_json=headers,
        payload_json=payload,
        status="received",
    )
    db.add(raw_event)
    db.flush()

    try:
        normalized_candidate = normalize_gcp_event(
            headers=headers,
            payload=payload,
            default_project_id=settings.default_gcp_project_id,
        )
        existing = (
            db.query(NormalizedEvent)
            .filter(NormalizedEvent.dedupe_key == normalized_candidate.dedupe_key)
            .one_or_none()
        )
        if existing is not None:
            raw_event.status = "duplicate"
            db.add(raw_event)
            db.commit()
            raise IngestionConflictError(
                f"Event with dedupe key '{normalized_candidate.dedupe_key}' already exists."
            )

        normalized_event = NormalizedEvent(
            raw_event_id=raw_event.id,
            source=normalized_candidate.source,
            event_type=normalized_candidate.event_type,
            severity=normalized_candidate.severity,
            project_id=normalized_candidate.project_id,
            region=normalized_candidate.region,
            resource_id=normalized_candidate.resource_id,
            resource_type=normalized_candidate.resource_type,
            dedupe_key=normalized_candidate.dedupe_key,
            occurred_at=normalized_candidate.occurred_at,
            metadata_json=normalized_candidate.metadata_json,
        )
        db.add(normalized_event)
        db.flush()

        matched_rules = get_matching_rules(db, normalized_event, settings.enable_rule_engine)
        workflow_runs = execute_workflows(db, normalized_event, matched_rules, settings)

        raw_event.status = "processed"
        db.add(raw_event)
        db.commit()
        db.refresh(raw_event)
        db.refresh(normalized_event)

        return EventIngestResponse(
            raw_event=raw_event,
            normalized_event=normalized_event,
            matched_rule_names=[rule.name for rule in matched_rules],
            workflow_runs=workflow_runs,
        )
    except IngestionConflictError:
        raise
    except Exception as exc:
        raw_event.status = "failed"
        raw_event.processing_error = str(exc)
        db.add(raw_event)
        db.commit()
        raise
