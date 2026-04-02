from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy import JSON, DateTime, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class RawEvent(Base):
    __tablename__ = "raw_events"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    provider: Mapped[str] = mapped_column(String(32), default="gcp")
    source: Mapped[str] = mapped_column(String(255))
    event_type: Mapped[str] = mapped_column(String(255))
    headers_json: Mapped[dict] = mapped_column(JSON, default=dict)
    payload_json: Mapped[dict] = mapped_column(JSON)
    status: Mapped[str] = mapped_column(String(32), default="received")
    processing_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    received_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
    )

    normalized_events: Mapped[list["NormalizedEvent"]] = relationship(
        "NormalizedEvent",
        back_populates="raw_event",
        cascade="all, delete-orphan",
    )
