"""Lightweight response types with an OpenAI chat-completion-like shape."""

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class GatekeeperMetadata:
    """Safety information attached to every allowed completion."""

    risk_score: int | None
    decision: str | None
    request_id: str | None
    categories: list[str]
    canary_triggered: bool = False


@dataclass(frozen=True)
class ChatCompletionMessage:
    role: str
    content: str


@dataclass(frozen=True)
class ChatCompletionChoice:
    index: int
    message: ChatCompletionMessage
    finish_reason: str = "stop"


@dataclass(frozen=True)
class CompletionUsage:
    prompt_tokens: int | None = None
    completion_tokens: int | None = None
    total_tokens: int | None = None


@dataclass
class GatekeeperChatCompletion:
    """An OpenAI-like chat completion returned by :meth:`GatekeeperClient.chat`."""

    id: str | None
    model: str
    choices: list[ChatCompletionChoice]
    usage: CompletionUsage | None
    provider: str
    gatekeeper_metadata: GatekeeperMetadata
    latency_ms: int | None = None
    object: str = "chat.completion"

    @property
    def content(self) -> str:
        """Convenience access to the first assistant response."""
        return self.choices[0].message.content

    def model_dump(self) -> dict[str, Any]:
        """Return a serializable OpenAI-style representation."""
        return {
            "id": self.id,
            "object": self.object,
            "model": self.model,
            "choices": [
                {
                    "index": choice.index,
                    "message": {"role": choice.message.role, "content": choice.message.content},
                    "finish_reason": choice.finish_reason,
                }
                for choice in self.choices
            ],
            "usage": None if self.usage is None else self.usage.__dict__.copy(),
        }

