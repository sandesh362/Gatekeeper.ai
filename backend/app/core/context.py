"""Request context shared across middleware, routes, and logging."""

from contextvars import ContextVar

request_id_ctx: ContextVar[str] = ContextVar("request_id", default="")
