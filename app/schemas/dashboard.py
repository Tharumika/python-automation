from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class DashboardEventCard(BaseModel):
    id: str
    event_type: str
    severity: str
    project_id: str
    resource_type: str | None
    resource_id: str | None
    occurred_at: datetime
    source: str


class DashboardWorkflowCard(BaseModel):
    id: str
    action_type: str
    status: str
    dry_run: bool
    started_at: datetime
    finished_at: datetime | None
    rule_id: str


class DashboardRuleCard(BaseModel):
    id: str
    name: str
    enabled: bool
    priority: int
    action_type: str
    severity_filter: str | None
    event_type_filter: str | None


class DashboardSummaryResponse(BaseModel):
    headline: str
    total_raw_events: int
    total_normalized_events: int
    enabled_rules: int
    total_rules: int
    total_workflow_runs: int
    severity_breakdown: dict[str, int]
    workflow_breakdown: dict[str, int]
    recent_events: list[DashboardEventCard]
    recent_workflow_runs: list[DashboardWorkflowCard]
    rules: list[DashboardRuleCard]
