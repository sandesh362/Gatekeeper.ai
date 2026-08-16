"""Unit tests for the risk aggregator."""

from app.features.detection.aggregator import aggregate_risk
from app.features.detection.schemas import (
    DetectionDecision,
    HeuristicResult,
    LLMJudgeResult,
    RuleMatch,
    SimilarityResult,
)


def test_aggregator_blocks_on_high_severity_rule() -> None:
    matches = [
        RuleMatch(
            rule_id="ignore_previous_instructions",
            severity=95,
            category="jailbreak",
            matched_text="ignore all previous instructions",
            description="test",
        )
    ]
    result = aggregate_risk(
        matches,
        SimilarityResult(),
        LLMJudgeResult(category="disabled"),
        HeuristicResult(),
    )
    assert result.risk_score >= 75
    assert result.decision == DetectionDecision.BLOCK
    assert "jailbreak" in result.categories


def test_aggregator_passes_benign() -> None:
    result = aggregate_risk(
        [],
        SimilarityResult(),
        LLMJudgeResult(malicious=False, confidence=0.1, category="benign"),
        HeuristicResult(),
    )
    assert result.decision == DetectionDecision.PASS
    assert result.risk_score < 40


def test_aggregator_flags_medium_risk() -> None:
    matches = [
        RuleMatch(
            rule_id="jailbreak_keyword",
            severity=70,
            category="jailbreak",
            matched_text="jailbreak",
            description="test",
        )
    ]
    result = aggregate_risk(
        matches,
        SimilarityResult(similarity_score=0.9, risk_level="high", category="jailbreak"),
        LLMJudgeResult(category="disabled"),
        HeuristicResult(score=80),
    )
    assert result.decision in (DetectionDecision.FLAG, DetectionDecision.BLOCK)
    assert result.risk_score >= 40


def test_aggregator_layer_breakdown_has_four_layers() -> None:
    result = aggregate_risk(
        [],
        SimilarityResult(),
        LLMJudgeResult(category="disabled"),
        HeuristicResult(),
    )
    assert len(result.layer_breakdown) == 4
