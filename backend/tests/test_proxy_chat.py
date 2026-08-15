"""Proxy chat endpoint tests."""

from unittest.mock import AsyncMock

import pytest
from fastapi.testclient import TestClient

from app.features.proxy.providers.base import ProviderError
from app.features.proxy.router import get_proxy_service
from app.main import app


def test_chat_completion_success(client_with_mock_proxy) -> None:
    response = client_with_mock_proxy.post(
        "/v1/chat",
        json={
            "provider": "openai",
            "model": "gpt-4o-mini",
            "messages": [{"role": "user", "content": "Say hello"}],
            "client_id": "test-client",
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["content"] == "Hello from Gatekeeper!"
    assert data["provider"] == "openai"
    assert data["latency_ms"] == 150
    assert data["usage"]["total_tokens"] == 15
    assert "X-Request-ID" in response.headers
    assert data["request_id"] == response.headers["X-Request-ID"]


def test_chat_validation_error(client_with_mock_proxy) -> None:
    response = client_with_mock_proxy.post(
        "/v1/chat",
        json={
            "provider": "openai",
            "model": "gpt-4o-mini",
            "messages": [],
        },
    )
    assert response.status_code == 422


def test_chat_provider_error() -> None:
    mock_service = AsyncMock()
    mock_service.handle_chat.side_effect = ProviderError("Rate limit exceeded", status_code=429)

    app.dependency_overrides[get_proxy_service] = lambda: mock_service
    with TestClient(app) as client:
        response = client.post(
            "/v1/chat",
            json={
                "provider": "openai",
                "model": "gpt-4o-mini",
                "messages": [{"role": "user", "content": "Hi"}],
            },
        )
    app.dependency_overrides.clear()

    assert response.status_code == 429
    data = response.json()
    assert data["error"] == "Provider request failed"
    assert data["detail"] == "Rate limit exceeded"
    assert "X-Request-ID" in response.headers


@pytest.mark.asyncio
async def test_openai_provider_parses_response() -> None:
    from unittest.mock import MagicMock, patch

    from app.features.proxy.providers.openai import OpenAIProvider

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "model": "gpt-4o-mini",
        "choices": [{"message": {"content": "Hi there"}}],
        "usage": {"prompt_tokens": 3, "completion_tokens": 4, "total_tokens": 7},
    }

    with patch("app.features.proxy.providers.openai.httpx.AsyncClient") as mock_client_cls:
        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_client.aclose = AsyncMock()
        mock_client_cls.return_value = mock_client

        provider = OpenAIProvider(api_key="test-key")
        result = await provider.chat_completion(
            "gpt-4o-mini",
            [{"role": "user", "content": "Hello"}],
        )

    assert result.content == "Hi there"
    assert result.total_tokens == 7
