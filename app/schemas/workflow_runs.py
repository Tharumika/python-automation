from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict

from app.schemas.events import NormalizedEventRead, RawEventRead
from app.schemas.rules import RuleRead


class WorkflowRunRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    normalized_event_id: str
    rule_id: str
    action_type: str
    status: str
    dry_run: bool
    result_payload: dict[str, Any]
    error_message: str | None
    started_at: datetime
    finished_at: datetime | None


class EventIngestResponse(BaseModel):
    raw_event: RawEventRead
    normalized_event: NormalizedEventRead
    matched_rule_names: list[str]
    workflow_runs: list[WorkflowRunRead]


class WorkflowRunDetailRead(WorkflowRunRead):
    normalized_event: NormalizedEventRead
    rule: RuleRead
