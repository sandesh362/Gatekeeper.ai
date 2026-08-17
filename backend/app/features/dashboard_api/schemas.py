"""Pydantic response models for the dashboard API."""

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field


Decision = Literal["pass", "flag", "block", "error"]


class RequestListItem(BaseModel):
    id: UUID
    timestamp: datetime
    provider: str
    model: str
    client_id: str | None
    decision: Decision
    risk_score: int | None
    latency_ms: int
    canary_triggered: bool = False


class PaginatedRequests(BaseModel):
    items: list[RequestListItem]
    page: int
    page_size: int
    total: int


class RequestDetail(RequestListItem):
    prompt: str
    response: str | None
    response_redacted: bool
    layer_breakdown: list[dict] = Field(default_factory=list)
    reasoning_summary: str | None = None
    error_message: str | None = None


class TimeBucket(BaseModel):
    hour: datetime
    pass_count: int = 0
    flag_count: int = 0
    block_count: int = 0
    error_count: int = 0


class DashboardStats(BaseModel):
    total_requests: int
    block_rate: float
    flag_rate: float
    average_latency_ms: float
    categories: dict[str, int]
    requests_over_time: list[TimeBucket]


class LiveRequestEvent(BaseModel):
    id: UUID
    timestamp: datetime
    decision: Decision
    risk_score: int | None
    provider: str
