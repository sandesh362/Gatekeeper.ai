"""Small in-process WebSocket fan-out for the live dashboard feed."""

import asyncio
from datetime import datetime
from uuid import UUID

from fastapi import WebSocket

from app.features.dashboard_api.schemas import LiveRequestEvent


class LiveDashboardHub:
    def __init__(self) -> None:
        self._connections: set[WebSocket] = set()

    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        self._connections.add(websocket)

    def disconnect(self, websocket: WebSocket) -> None:
        self._connections.discard(websocket)

    async def publish(
        self,
        *,
        request_id: UUID,
        timestamp: datetime,
        decision: str,
        risk_score: int | None,
        provider: str,
    ) -> None:
        event = LiveRequestEvent(
            id=request_id,
            timestamp=timestamp,
            decision=decision.lower(),
            risk_score=risk_score,
            provider=provider,
        ).model_dump_json()
        stale: list[WebSocket] = []
        for connection in list(self._connections):
            try:
                await connection.send_text(event)
            except Exception:  # a client may disconnect between broadcasts
                stale.append(connection)
        for connection in stale:
            self.disconnect(connection)


live_dashboard_hub = LiveDashboardHub()
