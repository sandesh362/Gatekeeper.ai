"""Pytest fixtures and helpers."""

import uuid
from collections.abc import Generator
from unittest.mock import AsyncMock

import pytest
from fastapi.testclient import TestClient

from app.features.proxy.router import get_proxy_service
from app.features.proxy.schemas import ChatRequest, ChatResponse, TokenUsage
from app.features.proxy.service import ProxyService
from app.main import app
from app.features.auth.dependencies import require_api_key


@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def mock_proxy_service() -> ProxyService:
    service = AsyncMock(spec=ProxyService)

    async def _handle_chat(
        request: ChatRequest, db, request_id: uuid.UUID, organization_id, api_key_id
    ) -> ChatResponse:
        return ChatResponse(
            request_id=str(request_id),
            provider=request.provider,
            model=request.model,
            content="Hello from Gatekeeper!",
            latency_ms=150,
            usage=TokenUsage(prompt_tokens=5, completion_tokens=10, total_tokens=15),
            detection=None,
        )

    service.handle_chat.side_effect = _handle_chat
    return service


@pytest.fixture(autouse=True)
def bypass_api_key_for_legacy_proxy_tests() -> Generator[None, None, None]:
    key = type("TestKey", (), {"organization_id": uuid.uuid4(), "id": uuid.uuid4()})()
    app.dependency_overrides[require_api_key] = lambda: key
    yield
    app.dependency_overrides.pop(require_api_key, None)


@pytest.fixture
def client_with_mock_proxy(mock_proxy_service: ProxyService) -> Generator[TestClient, None, None]:
    app.dependency_overrides[get_proxy_service] = lambda: mock_proxy_service
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
