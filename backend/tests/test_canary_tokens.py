"""Unit tests for canary token management."""

from app.features.detection.canary_tokens.manager import (
    check_canary_leakage,
    generate_canary_token,
    inject_canary_into_messages,
)


def test_generate_canary_token_unique() -> None:
    t1 = generate_canary_token("client-a")
    t2 = generate_canary_token("client-b")
    assert t1 != t2
    assert t1.startswith("GK_CANARY_")


def test_inject_canary_creates_system_message() -> None:
    messages = [{"role": "user", "content": "Hello"}]
    token = generate_canary_token()
    result = inject_canary_into_messages(messages, token)
    assert result[0]["role"] == "system"
    assert token in result[0]["content"]


def test_inject_canary_appends_to_existing_system() -> None:
    messages = [
        {"role": "system", "content": "You are helpful."},
        {"role": "user", "content": "Hi"},
    ]
    token = generate_canary_token()
    result = inject_canary_into_messages(messages, token)
    assert token in result[0]["content"]
    assert "You are helpful." in result[0]["content"]


def test_check_canary_leakage_detects_token() -> None:
    token = generate_canary_token()
    assert check_canary_leakage(f"The token is {token}", token) is True


def test_check_canary_leakage_clean_response() -> None:
    token = generate_canary_token()
    assert check_canary_leakage("Just a normal response.", token) is False
