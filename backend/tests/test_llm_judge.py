"""Unit tests for LLM judge response parsing."""

from app.features.detection.llm_judge.judge import _parse_judge_response


def test_parse_valid_json() -> None:
    raw = '{"malicious": true, "confidence": 0.95, "category": "jailbreak", "reasoning": "test"}'
    result = _parse_judge_response(raw)
    assert result.malicious is True
    assert result.confidence == 0.95
    assert result.category == "jailbreak"


def test_parse_json_embedded_in_text() -> None:
    raw = 'Here is my analysis: {"malicious": false, "confidence": 0.9, "category": "benign", "reasoning": "ok"}'
    result = _parse_judge_response(raw)
    assert result.malicious is False
    assert result.category == "benign"


def test_parse_invalid_returns_safe_default() -> None:
    result = _parse_judge_response("not json at all")
    assert result.malicious is False
    assert result.category == "unknown"
    assert result.confidence == 0.5
