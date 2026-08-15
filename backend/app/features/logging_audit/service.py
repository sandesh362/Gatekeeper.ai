"""Persist proxy transactions to the requests_log table."""

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Provider, RequestLog, RequestStatus
from app.features.logging_audit.logger import get_logger

logger = get_logger("gatekeeper.audit")


class AuditService:
    async def log_request(
        self,
        db: AsyncSession,
        *,
        request_id: uuid.UUID,
        client_id: str | None,
        provider: Provider,
        model_name: str,
        prompt: str,
        response: str | None,
        status: RequestStatus,
        latency_ms: int,
        error_message: str | None = None,
    ) -> RequestLog:
        entry = RequestLog(
            id=request_id,
            client_id=client_id,
            provider=provider,
            model_name=model_name,
            prompt=prompt,
            response=response,
            status=status,
            latency_ms=latency_ms,
            error_message=error_message,
        )
        db.add(entry)
        await db.commit()

        logger.info(
            "proxy_request_logged",
            extra={
                "provider": provider.value,
                "latency_ms": latency_ms,
                "status": status.value,
            },
        )
        return entry


audit_service = AuditService()
