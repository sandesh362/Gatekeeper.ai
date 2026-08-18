"""Exceptions raised by the Gatekeeper client."""


class GatekeeperError(Exception):
    """Base class for all Gatekeeper SDK exceptions."""


class GatekeeperConnectionError(GatekeeperError):
    """Gatekeeper could not be reached before a response was received."""

    def __init__(self, base_url: str, detail: str | None = None) -> None:
        hint = f" Check that Gatekeeper is running at {base_url}."
        message = f"Could not connect to Gatekeeper at {base_url}.{hint}"
        if detail:
            message = f"Could not connect to Gatekeeper at {base_url}: {detail}.{hint}"
        super().__init__(message)
        self.base_url = base_url


class GatekeeperBlockedError(GatekeeperError):
    """The request was blocked by Gatekeeper before it reached the provider."""

    def __init__(
        self,
        risk_score: int,
        category: str | None,
        request_id: str | None,
        *,
        categories: list[str] | None = None,
    ) -> None:
        self.risk_score = risk_score
        self.category = category
        self.categories = categories or ([] if category is None else [category])
        self.request_id = request_id
        super().__init__(
            "Request blocked "
            f"(risk_score={risk_score}, category={category or 'unknown'}, "
            f"request_id={request_id or 'unknown'}). See dashboard for details."
        )


class GatekeeperAPIError(GatekeeperError):
    """Gatekeeper returned an unexpected non-success HTTP response."""

    def __init__(self, status_code: int, detail: str, request_id: str | None = None) -> None:
        self.status_code = status_code
        self.detail = detail
        self.request_id = request_id
        suffix = f" (request_id={request_id})" if request_id else ""
        super().__init__(f"Gatekeeper API error ({status_code}): {detail}{suffix}")

