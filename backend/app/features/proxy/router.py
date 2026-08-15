"""Proxy HTTP routes."""

import uuid

from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.features.proxy.providers.base import ProviderError
from app.features.proxy.schemas import ChatErrorResponse, ChatRequest, ChatResponse
from app.features.proxy.service import ProxyService, proxy_service

router = APIRouter(tags=["proxy"])


def get_proxy_service() -> ProxyService:
    return proxy_service


@router.post("/chat", response_model=ChatResponse)
async def chat_completion(
    body: ChatRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    service: ProxyService = Depends(get_proxy_service),
) -> ChatResponse | JSONResponse:
    request_id = uuid.UUID(request.state.request_id)

    try:
        return await service.handle_chat(body, db, request_id)
    except ProviderError as exc:
        return JSONResponse(
            status_code=exc.status_code,
            content=ChatErrorResponse(
                request_id=str(request_id),
                error="Provider request failed",
                detail=exc.message,
            ).model_dump(),
            headers={"X-Request-ID": str(request_id)},
        )
