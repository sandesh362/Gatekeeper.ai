"""Phase 6 security regressions that do not require external services."""
from datetime import timedelta

from fastapi.testclient import TestClient

from app.core.security import create_token, decode_token, hash_api_key
from app.features.auth.dependencies import require_api_key
from app.main import app


def test_chat_without_api_key_is_rejected() -> None:
    app.dependency_overrides.pop(require_api_key, None)
    with TestClient(app) as client:
        response = client.post("/v1/chat", json={"provider": "openai", "model": "gpt-4o-mini", "messages": [{"role": "user", "content": "Hi"}]})
    assert response.status_code == 401


def test_api_key_hash_is_deterministic_and_not_plaintext() -> None:
    assert hash_api_key("gk_example") == hash_api_key("gk_example")
    assert hash_api_key("gk_example") != "gk_example"


def test_access_tokens_cannot_be_used_as_refresh_tokens() -> None:
    token = create_token("user", "organization", "access", timedelta(minutes=1))
    try:
        decode_token(token, "refresh")
    except ValueError:
        pass
    else:
        raise AssertionError("access token was accepted as a refresh token")
