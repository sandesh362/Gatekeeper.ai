"""Persist detection results to the detection_results table."""

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import DetectionDecisionEnum, DetectionResultRecord
from app.features.detection.schemas import DetectionResult
from app.features.logging_audit.logger import get_logger

logger = get_logger("gatekeeper.detection.audit")


class DetectionAuditService:
    async def log_detection(
        self,
        db: AsyncSession,
        *,
        request_id: uuid.UUID,
        result: DetectionResult,
    ) -> DetectionResultRecord:
        existing = await db.execute(
            select(DetectionResultRecord).where(DetectionResultRecord.request_id == request_id)
        )
        record = existing.scalar_one_or_none()

        if record is None:
            record = DetectionResultRecord(request_id=request_id)
            db.add(record)

        record.risk_score = result.risk_score
        record.decision = DetectionDecisionEnum(result.decision.value)
        record.layer_breakdown = [layer.model_dump() for layer in result.layer_breakdown]
        record.canary_triggered = result.canary_triggered
        record.reasoning_summary = result.reasoning_summary

        await db.commit()

        logger.info(
            "detection_result_logged",
            extra={
                "risk_score": result.risk_score,
                "decision": result.decision.value,
                "canary_triggered": result.canary_triggered,
            },
        )
        return record


detection_audit_service = DetectionAuditService()
