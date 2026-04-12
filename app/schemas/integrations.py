from __future__ import annotations

from pydantic import BaseModel


class IntegrationStatusResponse(BaseModel):
    mode: str
    dry_run: bool
    slack_configured: bool
    slack_destination_label: str
    notification_webhook_configured: bool
    incident_webhook_configured: bool


class IntegrationTestResponse(BaseModel):
    test_type: str
    queue_processed: bool
    workflow_run_id: str
    workflow_status: str
    delivery: str
    connector_type: str
    destination_label: str
