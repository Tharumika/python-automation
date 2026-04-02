from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy import JSON, DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class NormalizedEvent(Base):
    __tablename__ = "normalized_events"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    raw_event_id: Mapped[str] = mapped_column(ForeignKey("raw_events.id"), index=True)
    source: Mapped[str] = mapped_column(String(255))
    event_type: Mapped[str] = mapped_column(String(255), index=True)
    severity: Mapped[str] = mapped_column(String(32), index=True)
    project_id: Mapped[str] = mapped_column(String(128), index=True)
    region: Mapped[str | None] = mapped_column(String(128), nullable=True)
    resource_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    resource_type: Mapped[str | None] = mapped_column(String(128), nullable=True)
    dedupe_key: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
    )

    raw_event: Mapped["RawEvent"] = relationship("RawEvent", back_populates="normalized_events")
    workflow_runs: Mapped[list["WorkflowRun"]] = relationship(
        "WorkflowRun",
        back_populates="normalized_event",
        cascade="all, delete-orphan",
    )
