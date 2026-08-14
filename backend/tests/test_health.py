"""Smoke tests for Phase 1 scaffold."""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_check() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_api_v1_root() -> None:
    response = client.get("/api/v1/")
    assert response.status_code == 200
    assert "Gatekeeper" in response.json()["message"]
