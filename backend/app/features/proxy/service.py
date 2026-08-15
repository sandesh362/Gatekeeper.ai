"""Core proxy orchestration — forward to LLM and audit the transaction."""

import time
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Provider, RequestStatus
from app.features.logging_audit.logger import get_logger
from app.features.logging_audit.service import AuditService, audit_service
from app.features.proxy.providers.base import ProviderClient, ProviderError
from app.features.proxy.providers.factory import get_provider
from app.features.proxy.schemas import ChatRequest, ChatResponse, TokenUsage

logger = get_logger("gatekeeper.proxy")


class ProxyService:
    def __init__(self, audit: AuditService | None = None) -> None:
        self._audit = audit or audit_service

    async def handle_chat(
        self,
        request: ChatRequest,
        db: AsyncSession,
        request_id: uuid.UUID,
    ) -> ChatResponse:
        provider_client = get_provider(request.provider)
        messages = [message.model_dump() for message in request.messages]
        prompt_text = _serialize_prompt(messages)
        provider_enum = Provider(request.provider)

        start = time.perf_counter()
        try:
            result = await provider_client.chat_completion(
                request.model,
                messages,
                max_tokens=request.max_tokens,
            )
            latency_ms = int((time.perf_counter() - start) * 1000)

            await self._audit.log_request(
                db,
                request_id=request_id,
                client_id=request.client_id,
                provider=provider_enum,
                model_name=result.model,
                prompt=prompt_text,
                response=result.content,
                status=RequestStatus.success,
                latency_ms=latency_ms,
            )

            logger.info(
                "proxy_request_completed",
                extra={
                    "provider": request.provider,
                    "latency_ms": latency_ms,
                    "status": RequestStatus.success.value,
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
            )
        except ProviderError as exc:
            latency_ms = int((time.perf_counter() - start) * 1000)
            await self._audit.log_request(
                db,
                request_id=request_id,
                client_id=request.client_id,
                provider=provider_enum,
                model_name=request.model,
                prompt=prompt_text,
                response=None,
                status=RequestStatus.error,
                latency_ms=latency_ms,
                error_message=exc.message,
            )
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


def _serialize_prompt(messages: list[dict[str, str]]) -> str:
    return "\n".join(f"{message['role']}: {message['content']}" for message in messages)


proxy_service = ProxyService()
