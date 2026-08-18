"""OpenAI-shaped compatibility wrapper with no OpenAI SDK dependency.

Use ``from gatekeeper_ai.compat import GatekeeperOpenAI as OpenAI`` to retain
the familiar ``client.chat.completions.create(...)`` call site.
"""

from __future__ import annotations

from typing import Any

from .client import GatekeeperClient


class _ChatCompletions:
    def __init__(self, client: GatekeeperClient) -> None:
        self._client = client

    def create(self, *, model: str, messages: list[dict[str, Any]], **kwargs: Any) -> Any:
        return self._client.chat(messages=messages, model=model, **kwargs)


class _Chat:
    def __init__(self, client: GatekeeperClient) -> None:
        self.completions = _ChatCompletions(client)


class GatekeeperOpenAI:
    """A compact replacement for the OpenAI client chat-completions surface.

    The constructor accepts the familiar ``api_key`` and ``base_url`` arguments.
    Here ``base_url`` means the Gatekeeper proxy URL, not api.openai.com.
    """

    def __init__(self, *, api_key: str | None = None, base_url: str | None = None, **kwargs: Any) -> None:
        timeout = kwargs.pop("timeout", 60.0)
        if kwargs:
            unsupported = ", ".join(sorted(kwargs))
            raise TypeError(f"Unsupported GatekeeperOpenAI argument(s): {unsupported}")
        self._gatekeeper = GatekeeperClient(base_url=base_url, api_key=api_key, provider="openai", timeout=timeout)
        self.chat = _Chat(self._gatekeeper)

    def close(self) -> None:
        self._gatekeeper.close()

    def __enter__(self) -> GatekeeperOpenAI:
        return self

    def __exit__(self, *_: Any) -> None:
        self.close()

