"""Pydantic schemas for the proxy chat endpoint."""

from typing import Literal

from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    role: Literal["system", "user", "assistant"]
    content: str


class ChatRequest(BaseModel):
    provider: Literal["openai", "anthropic"]
    model: str = Field(..., min_length=1)
    messages: list[ChatMessage] = Field(..., min_length=1)
    client_id: str | None = None
    max_tokens: int | None = Field(default=None, ge=1)


class TokenUsage(BaseModel):
    prompt_tokens: int | None = None
    completion_tokens: int | None = None
    total_tokens: int | None = None


class DetectionMetadata(BaseModel):
    risk_score: int
    decision: str
    categories: list[str] = Field(default_factory=list)
    canary_triggered: bool = False


class ChatResponse(BaseModel):
    request_id: str
    provider: str
    model: str
    content: str
    latency_ms: int
    usage: TokenUsage | None = None
    detection: DetectionMetadata | None = None


class ChatErrorResponse(BaseModel):
    request_id: str
    error: str
    detail: str


class BlockedResponse(BaseModel):
    request_id: str
    error: str = "Request blocked"
    risk_score: int
    categories: list[str] = Field(default_factory=list)
