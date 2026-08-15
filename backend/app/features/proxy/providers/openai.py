"""OpenAI-compatible chat completions provider."""

import httpx

from app.core.config import settings
from app.features.proxy.providers.base import CompletionResult, ProviderClient, ProviderError

OPENAI_CHAT_URL = "https://api.openai.com/v1/chat/completions"


class OpenAIProvider(ProviderClient):
    def __init__(self, api_key: str | None = None) -> None:
        self._api_key = api_key or settings.OPENAI_API_KEY
        self._client = httpx.AsyncClient(timeout=60.0)

    async def chat_completion(
        self,
        model: str,
        messages: list[dict[str, str]],
        *,
        max_tokens: int | None = None,
    ) -> CompletionResult:
        if not self._api_key:
            raise ProviderError("OpenAI API key is not configured", status_code=500)

        payload: dict = {"model": model, "messages": messages}
        if max_tokens is not None:
            payload["max_tokens"] = max_tokens

        try:
            response = await self._client.post(
                OPENAI_CHAT_URL,
                headers={
                    "Authorization": f"Bearer {self._api_key}",
                    "Content-Type": "application/json",
                },
                json=payload,
            )
        except httpx.TimeoutException:
            raise ProviderError("OpenAI request timed out", status_code=504) from None
        except httpx.RequestError:
            raise ProviderError("Failed to reach OpenAI API", status_code=502) from None

        if response.status_code != 200:
            raise ProviderError(
                _extract_error_message(response, "OpenAI request failed"),
                status_code=response.status_code if response.status_code < 500 else 502,
            )

        data = response.json()
        try:
            content = data["choices"][0]["message"]["content"] or ""
        except (KeyError, IndexError, TypeError):
            raise ProviderError("Unexpected response format from OpenAI", status_code=502)

        usage = data.get("usage") or {}
        return CompletionResult(
            content=content,
            model=data.get("model", model),
            prompt_tokens=usage.get("prompt_tokens"),
            completion_tokens=usage.get("completion_tokens"),
            total_tokens=usage.get("total_tokens"),
        )

    async def close(self) -> None:
        await self._client.aclose()


def _extract_error_message(response: httpx.Response, fallback: str) -> str:
    try:
        data = response.json()
        error = data.get("error", {})
        if isinstance(error, dict) and error.get("message"):
            return str(error["message"])
        if isinstance(error, str):
            return error
    except Exception:
        pass
    return fallback
