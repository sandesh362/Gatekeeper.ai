"""Core proxy orchestration — detection, forward to LLM, and audit."""

import time
import uuid
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Provider, RequestStatus
from app.features.detection.canary_tokens.manager import (
    check_canary_leakage,
    generate_canary_token,
    inject_canary_into_messages,
)
from app.features.detection.schemas import DetectionDecision
from app.features.detection.service import DetectionService, detection_service
from app.features.logging_audit.detection_audit import DetectionAuditService, detection_audit_service
from app.features.logging_audit.logger import get_logger
from app.features.logging_audit.service import AuditService, audit_service
from app.features.dashboard_api.live import live_dashboard_hub
from app.features.proxy.providers.base import ProviderError
from app.features.proxy.providers.factory import get_provider
from app.features.proxy.schemas import ChatRequest, ChatResponse, DetectionMetadata, TokenUsage

logger = get_logger("gatekeeper.proxy")


class ProxyBlockedError(Exception):
    def __init__(self, risk_score: int, categories: list[str]) -> None:
        self.risk_score = risk_score
        self.categories = categories
        super().__init__(f"Request blocked (risk_score={risk_score})")


class ProxyService:
    def __init__(
        self,
        audit: AuditService | None = None,
        detection: DetectionService | None = None,
        detection_audit: DetectionAuditService | None = None,
    ) -> None:
        self._audit = audit or audit_service
        self._detection = detection or detection_service
        self._detection_audit = detection_audit or detection_audit_service

    async def handle_chat(
        self,
        request: ChatRequest,
        db: AsyncSession,
        request_id: uuid.UUID,
        organization_id: uuid.UUID,
        api_key_id: uuid.UUID,
    ) -> ChatResponse:
        provider_client = get_provider(request.provider)
        messages = [message.model_dump() for message in request.messages]
        prompt_text = _serialize_prompt(messages)
        detection_text = _extract_detection_text(messages)
        provider_enum = Provider(request.provider)

        start = time.perf_counter()

        detection_result = await self._detection.analyze_prompt(detection_text)

        if detection_result.decision == DetectionDecision.BLOCK:
            latency_ms = int((time.perf_counter() - start) * 1000)
            entry = await self._audit.log_request(
                db,
                request_id=request_id,
                organization_id=organization_id, api_key_id=api_key_id,
                provider=provider_enum,
                model_name=request.model,
                prompt=prompt_text,
                response=None,
                status=RequestStatus.blocked,
                latency_ms=latency_ms,
                error_message=detection_result.reasoning_summary,
            )
            await self._detection_audit.log_detection(db, request_id=request_id, organization_id=organization_id, result=detection_result)
            await self._publish_live(entry, detection_result, organization_id)
            logger.warning(
                "proxy_request_blocked",
                extra={
                    "risk_score": detection_result.risk_score,
                    "categories": detection_result.categories,
                },
            )
            raise ProxyBlockedError(
                risk_score=detection_result.risk_score,
                categories=detection_result.categories,
            )

        canary_token = generate_canary_token(str(organization_id))
        messages_with_canary = inject_canary_into_messages(messages, canary_token)

        try:
            result = await provider_client.chat_completion(
                request.model,
                messages_with_canary,
                max_tokens=request.max_tokens,
            )
            latency_ms = int((time.perf_counter() - start) * 1000)

            if check_canary_leakage(result.content, canary_token):
                detection_result = self._detection.apply_canary_block(detection_result)
                entry = await self._audit.log_request(
                    db,
                    request_id=request_id,
                    organization_id=organization_id, api_key_id=api_key_id,
                    provider=provider_enum,
                    model_name=result.model,
                    prompt=prompt_text,
                    response=result.content,
                    status=RequestStatus.blocked,
                    latency_ms=latency_ms,
                    error_message=detection_result.reasoning_summary,
                )
                await self._detection_audit.log_detection(
                    db, request_id=request_id, organization_id=organization_id, result=detection_result
                )
                await self._publish_live(entry, detection_result, organization_id)
                raise ProxyBlockedError(
                    risk_score=detection_result.risk_score,
                    categories=detection_result.categories,
                )

            entry = await self._audit.log_request(
                db,
                request_id=request_id,
                organization_id=organization_id, api_key_id=api_key_id,
                provider=provider_enum,
                model_name=result.model,
                prompt=prompt_text,
                response=result.content,
                status=RequestStatus.success,
                latency_ms=latency_ms,
            )
            await self._detection_audit.log_detection(db, request_id=request_id, organization_id=organization_id, result=detection_result)
            await self._publish_live(entry, detection_result, organization_id)

            logger.info(
                "proxy_request_completed",
                extra={
                    "provider": request.provider,
                    "latency_ms": latency_ms,
                    "status": RequestStatus.success.value,
                    "risk_score": detection_result.risk_score,
                },
            )

            return ChatResponse(
                request_id=str(request_id),
                provider=request.provider,
                model=result.model,
                content=result.content,
                latency_ms=latency_ms,
                usage=TokenUsage(
                    prompt_tokens=result.prompt_tokens,
                    completion_tokens=result.completion_tokens,
                    total_tokens=result.total_tokens,
                ),
                detection=DetectionMetadata(
                    risk_score=detection_result.risk_score,
                    decision=detection_result.decision.value,
                    categories=detection_result.categories,
                    canary_triggered=detection_result.canary_triggered,
                ),
            )
        except ProviderError as exc:
            latency_ms = int((time.perf_counter() - start) * 1000)
            entry = await self._audit.log_request(
                db,
                request_id=request_id,
                organization_id=organization_id, api_key_id=api_key_id,
                provider=provider_enum,
                model_name=request.model,
                prompt=prompt_text,
                response=None,
                status=RequestStatus.error,
                latency_ms=latency_ms,
                error_message=exc.message,
            )
            await self._detection_audit.log_detection(db, request_id=request_id, organization_id=organization_id, result=detection_result)
            await self._publish_live(entry, None, organization_id)
            logger.warning(
                "proxy_request_failed",
                extra={
                    "provider": request.provider,
                    "latency_ms": latency_ms,
                    "status": RequestStatus.error.value,
                },
            )
            raise
        finally:
            await provider_client.close()

    @staticmethod
    async def _publish_live(entry, detection_result, organization_id: uuid.UUID) -> None:
        """Notify dashboard clients after the durable audit write succeeds."""
        await live_dashboard_hub.publish(
            request_id=entry.id,
            timestamp=entry.timestamp or datetime.now(timezone.utc),
            decision=(detection_result.decision.value if detection_result else "error"),
            risk_score=detection_result.risk_score if detection_result else None,
            provider=entry.provider.value,
            organization_id=organization_id,
        )


def _serialize_prompt(messages: list[dict[str, str]]) -> str:
    return "\n".join(f"{message['role']}: {message['content']}" for message in messages)


def _extract_detection_text(messages: list[dict[str, str]]) -> str:
    """Extract user-supplied content for detection (without role prefixes)."""
    user_parts = [m["content"] for m in messages if m["role"] == "user"]
    if user_parts:
        return "\n".join(user_parts)
    return "\n".join(m["content"] for m in messages)


proxy_service = ProxyService()
