from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class RuleBase(BaseModel):
    name: str
    description: str | None = None
    source_filter: str | None = None
    event_type_filter: str | None = None
    severity_filter: str | None = None
    resource_type_filter: str | None = None
    conditions_json: dict[str, Any] = Field(default_factory=dict)
    action_type: str = "notify"
    action_target: str | None = None
    enabled: bool = True
    priority: int = 100


class RuleCreate(RuleBase):
    pass


class RuleUpdate(BaseModel):
    description: str | None = None
    source_filter: str | None = None
    event_type_filter: str | None = None
    severity_filter: str | None = None
    resource_type_filter: str | None = None
    conditions_json: dict[str, Any] | None = None
    action_type: str | None = None
    action_target: str | None = None
    enabled: bool | None = None
    priority: int | None = None


class RuleRead(RuleBase):
    model_config = ConfigDict(from_attributes=True)

    id: str
    created_at: datetime

