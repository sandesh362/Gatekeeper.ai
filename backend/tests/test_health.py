"""Health check endpoint tests."""

from unittest.mock import AsyncMock, patch

from tests.conftest import client


@patch("app.api.health.check_db_connection", new_callable=AsyncMock, return_value=True)
def test_health_check_db_connected(_mock_db: AsyncMock, client) -> None:
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["db"] == "connected"


@patch("app.api.health.check_db_connection", new_callable=AsyncMock, return_value=False)
def test_health_check_db_disconnected(_mock_db: AsyncMock, client) -> None:
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["db"] == "disconnected"
