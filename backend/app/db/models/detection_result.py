"""Detection result ORM model."""

import enum
import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class DetectionDecisionEnum(str, enum.Enum):
    PASS = "PASS"
    FLAG = "FLAG"
    BLOCK = "BLOCK"


class DetectionResultRecord(Base):
    __tablename__ = "detection_results"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    request_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("requests_log.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    organization_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False, index=True)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    risk_score: Mapped[int] = mapped_column(Integer, nullable=False)
    decision: Mapped[DetectionDecisionEnum] = mapped_column(
        Enum(DetectionDecisionEnum, name="detection_decision_enum"), nullable=False
    )
    layer_breakdown: Mapped[dict] = mapped_column(JSONB, nullable=False)
    canary_triggered: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    reasoning_summary: Mapped[str] = mapped_column(Text, nullable=False)
