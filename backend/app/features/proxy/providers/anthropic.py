"""Anthropic Messages API provider."""

import httpx

from app.core.config import settings
from app.features.proxy.providers.base import CompletionResult, ProviderClient, ProviderError
from app.features.proxy.providers.openai import _extract_error_message

ANTHROPIC_MESSAGES_URL = "https://api.anthropic.com/v1/messages"
ANTHROPIC_VERSION = "2023-06-01"
DEFAULT_MAX_TOKENS = 1024


class AnthropicProvider(ProviderClient):
    def __init__(self, api_key: str | None = None) -> None:
        self._api_key = api_key or settings.ANTHROPIC_API_KEY
        self._client = httpx.AsyncClient(timeout=60.0)

    async def chat_completion(
        self,
        model: str,
        messages: list[dict[str, str]],
        *,
        max_tokens: int | None = None,
    ) -> CompletionResult:
        if not self._api_key:
            raise ProviderError("Anthropic API key is not configured", status_code=500)

        system_prompt, api_messages = _split_system_messages(messages)
        payload: dict = {
            "model": model,
            "max_tokens": max_tokens or DEFAULT_MAX_TOKENS,
            "messages": api_messages,
        }
        if system_prompt:
            payload["system"] = system_prompt

        try:
            response = await self._client.post(
                ANTHROPIC_MESSAGES_URL,
                headers={
                    "x-api-key": self._api_key,
                    "anthropic-version": ANTHROPIC_VERSION,
                    "Content-Type": "application/json",
                },
                json=payload,
            )
        except httpx.TimeoutException:
            raise ProviderError("Anthropic request timed out", status_code=504) from None
        except httpx.RequestError:
            raise ProviderError("Failed to reach Anthropic API", status_code=502) from None

        if response.status_code != 200:
            raise ProviderError(
                _extract_error_message(response, "Anthropic request failed"),
                status_code=response.status_code if response.status_code < 500 else 502,
            )

        data = response.json()
        try:
            content = data["content"][0]["text"]
        except (KeyError, IndexError, TypeError):
            raise ProviderError("Unexpected response format from Anthropic", status_code=502)

        usage = data.get("usage") or {}
        return CompletionResult(
            content=content,
            model=data.get("model", model),
            prompt_tokens=usage.get("input_tokens"),
            completion_tokens=usage.get("output_tokens"),
            total_tokens=(usage.get("input_tokens") or 0) + (usage.get("output_tokens") or 0),
        )

    async def close(self) -> None:
        await self._client.aclose()


def _split_system_messages(
    messages: list[dict[str, str]],
) -> tuple[str | None, list[dict[str, str]]]:
    system_parts: list[str] = []
    api_messages: list[dict[str, str]] = []

    for message in messages:
        role = message.get("role", "user")
        content = message.get("content", "")
        if role == "system":
            system_parts.append(content)
        else:
            api_messages.append({"role": role, "content": content})

    system_prompt = "\n\n".join(system_parts) if system_parts else None
    return system_prompt, api_messages
