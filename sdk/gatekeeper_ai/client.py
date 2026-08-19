"""Synchronous and asynchronous clients for the Gatekeeper proxy."""

from __future__ import annotations

import os
from typing import Any

import httpx

from .exceptions import GatekeeperAPIError, GatekeeperAuthError, GatekeeperBlockedError, GatekeeperConnectionError, GatekeeperRateLimitError
from .types import (
    ChatCompletionChoice,
    ChatCompletionMessage,
    CompletionUsage,
    GatekeeperChatCompletion,
    GatekeeperMetadata,
)

DEFAULT_BASE_URL = "http://localhost:8000"


def _settings(base_url: str | None, api_key: str | None) -> tuple[str, str | None]:
    resolved_url = base_url or os.getenv("GATEKEEPER_BASE_URL") or DEFAULT_BASE_URL
    return resolved_url.rstrip("/"), api_key if api_key is not None else os.getenv("GATEKEEPER_API_KEY")


def _headers(api_key: str | None) -> dict[str, str]:
    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
        headers["X-API-Key"] = api_key
    return headers


def _payload(provider: str, messages: list[dict[str, Any]], model: str, kwargs: dict[str, Any]) -> dict[str, Any]:
    payload: dict[str, Any] = {"provider": provider, "model": model, "messages": messages}
    # These are the optional request fields currently accepted by Gatekeeper's /v1/chat API.
    for key in ("max_tokens", "client_id"):
        if key in kwargs and kwargs[key] is not None:
            payload[key] = kwargs.pop(key)
    if kwargs:
        unsupported = ", ".join(sorted(kwargs))
        raise TypeError(
            f"Unsupported Gatekeeper chat argument(s): {unsupported}. "
            "The current proxy supports max_tokens and client_id."
        )
    return payload


def _error_detail(data: Any, fallback: str) -> str:
    if isinstance(data, dict):
        return str(data.get("detail") or data.get("error") or fallback)
    return fallback


def _handle_response(response: httpx.Response) -> GatekeeperChatCompletion:
    try:
        data = response.json()
    except ValueError:
        data = {}
    request_id = response.headers.get("X-Request-ID") or (data.get("request_id") if isinstance(data, dict) else None)

    if response.status_code == 403:
        categories = data.get("categories", []) if isinstance(data, dict) else []
        category = categories[0] if categories else None
        risk_score = data.get("risk_score", 0) if isinstance(data, dict) else 0
        raise GatekeeperBlockedError(risk_score, category, request_id, categories=categories)
    if response.status_code == 401:
        raise GatekeeperAuthError()
    if response.status_code == 429:
        raw_retry = response.headers.get("Retry-After")
        raise GatekeeperRateLimitError(int(raw_retry) if raw_retry and raw_retry.isdigit() else None)
    if response.is_error:
        raise GatekeeperAPIError(response.status_code, _error_detail(data, response.reason_phrase), request_id)

    detection = data.get("detection") or {}
    metadata = GatekeeperMetadata(
        risk_score=detection.get("risk_score"),
        decision=detection.get("decision"),
        request_id=data.get("request_id") or request_id,
        categories=detection.get("categories") or [],
        canary_triggered=detection.get("canary_triggered", False),
    )
    raw_usage = data.get("usage")
    usage = CompletionUsage(**raw_usage) if raw_usage else None
    return GatekeeperChatCompletion(
        id=data.get("request_id") or request_id,
        model=data.get("model", ""),
        provider=data.get("provider", ""),
        choices=[ChatCompletionChoice(0, ChatCompletionMessage("assistant", data.get("content", "")))],
        usage=usage,
        gatekeeper_metadata=metadata,
        latency_ms=data.get("latency_ms"),
    )


class GatekeeperClient:
    """Synchronous client for Gatekeeper's ``POST /v1/chat`` endpoint."""

    def __init__(
        self,
        base_url: str | None = None,
        api_key: str | None = None,
        provider: str = "openai",
        *,
        timeout: float | httpx.Timeout = 60.0,
        http_client: httpx.Client | None = None,
    ) -> None:
        self.base_url, self.api_key = _settings(base_url, api_key)
        if not self.api_key:
            raise GatekeeperAuthError()
        self.provider = provider
        self._client = http_client or httpx.Client(timeout=timeout)
        self._owns_client = http_client is None

    def chat(self, messages: list[dict[str, Any]], model: str, **kwargs: Any) -> GatekeeperChatCompletion:
        """Create a protected chat completion.

        ``messages``, ``model``, and ``max_tokens`` follow OpenAI's chat-completions
        conventions. A blocked prompt raises :class:`GatekeeperBlockedError`.
        """
        payload = _payload(self.provider, messages, model, kwargs)
        try:
            response = self._client.post(f"{self.base_url}/v1/chat", json=payload, headers=_headers(self.api_key))
        except (httpx.TimeoutException, httpx.RequestError) as exc:
            raise GatekeeperConnectionError(self.base_url, str(exc)) from exc
        return _handle_response(response)

    def close(self) -> None:
        if self._owns_client:
            self._client.close()

    def __enter__(self) -> GatekeeperClient:
        return self

    def __exit__(self, *_: Any) -> None:
        self.close()


class AsyncGatekeeperClient:
    """Asynchronous client for Gatekeeper's ``POST /v1/chat`` endpoint."""

    def __init__(
        self,
        base_url: str | None = None,
        api_key: str | None = None,
        provider: str = "openai",
        *,
        timeout: float | httpx.Timeout = 60.0,
        http_client: httpx.AsyncClient | None = None,
    ) -> None:
        self.base_url, self.api_key = _settings(base_url, api_key)
        if not self.api_key:
            raise GatekeeperAuthError()
        self.provider = provider
        self._client = http_client or httpx.AsyncClient(timeout=timeout)
        self._owns_client = http_client is None

    async def chat(self, messages: list[dict[str, Any]], model: str, **kwargs: Any) -> GatekeeperChatCompletion:
        payload = _payload(self.provider, messages, model, kwargs)
        try:
            response = await self._client.post(f"{self.base_url}/v1/chat", json=payload, headers=_headers(self.api_key))
        except (httpx.TimeoutException, httpx.RequestError) as exc:
            raise GatekeeperConnectionError(self.base_url, str(exc)) from exc
        return _handle_response(response)

    async def aclose(self) -> None:
        if self._owns_client:
            await self._client.aclose()

    async def __aenter__(self) -> AsyncGatekeeperClient:
        return self

    async def __aexit__(self, *_: Any) -> None:
        await self.aclose()
