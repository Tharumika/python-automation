from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy import JSON, Boolean, DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Rule(Base):
    __tablename__ = "rules"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    name: Mapped[str] = mapped_column(String(255), unique=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    source_filter: Mapped[str | None] = mapped_column(String(255), nullable=True)
    event_type_filter: Mapped[str | None] = mapped_column(String(255), nullable=True)
    severity_filter: Mapped[str | None] = mapped_column(String(255), nullable=True)
    resource_type_filter: Mapped[str | None] = mapped_column(String(128), nullable=True)
    conditions_json: Mapped[dict] = mapped_column(JSON, default=dict)
    action_type: Mapped[str] = mapped_column(String(64), default="notify")
    action_target: Mapped[str | None] = mapped_column(String(255), nullable=True)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    priority: Mapped[int] = mapped_column(Integer, default=100)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
    )

    workflow_runs: Mapped[list["WorkflowRun"]] = relationship(
        "WorkflowRun",
        back_populates="rule",
    )
