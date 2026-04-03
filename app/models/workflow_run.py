from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy import JSON, Boolean, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class WorkflowRun(Base):
    __tablename__ = "workflow_runs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    normalized_event_id: Mapped[str] = mapped_column(
        ForeignKey("normalized_events.id"),
        index=True,
    )
    rule_id: Mapped[str] = mapped_column(ForeignKey("rules.id"), index=True)
    action_type: Mapped[str] = mapped_column(String(64))
    status: Mapped[str] = mapped_column(String(32), index=True)
    dry_run: Mapped[bool] = mapped_column(Boolean, default=True)
    result_payload: Mapped[dict] = mapped_column(JSON, default=dict)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
    )
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    normalized_event: Mapped["NormalizedEvent"] = relationship(
        "NormalizedEvent",
        back_populates="workflow_runs",
    )
    rule: Mapped["Rule"] = relationship("Rule", back_populates="workflow_runs")
    workflow_task: Mapped["WorkflowTask | None"] = relationship(
        "WorkflowTask",
        back_populates="workflow_run",
        cascade="all, delete-orphan",
        uselist=False,
    )
