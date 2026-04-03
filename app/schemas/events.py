from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class RawEventRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    provider: str
    source: str
    event_type: str
    headers_json: dict[str, Any]
    payload_json: dict[str, Any]
    status: str
    processing_error: str | None
    received_at: datetime


class NormalizedEventCandidate(BaseModel):
    source: str
    event_type: str
    severity: str
    project_id: str
    region: str | None = None
    resource_id: str | None = None
    resource_type: str | None = None
    occurred_at: datetime
    dedupe_key: str
    metadata_json: dict[str, Any] = Field(default_factory=dict)


class NormalizedEventRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    raw_event_id: str
    source: str
    event_type: str
    severity: str
    project_id: str
    region: str | None
    resource_id: str | None
    resource_type: str | None
    dedupe_key: str
    occurred_at: datetime
    metadata_json: dict[str, Any]
    created_at: datetime


class EventWorkflowSummary(BaseModel):
    id: str
    action_type: str
    status: str
    dry_run: bool
    started_at: datetime
    rule_id: str


class NormalizedEventDetailRead(NormalizedEventRead):
    raw_event: RawEventRead
    workflow_runs: list[EventWorkflowSummary]
