"""Shared Pydantic schemas for the detection engine."""

from enum import Enum

from pydantic import BaseModel, Field


class DetectionDecision(str, Enum):
    PASS = "PASS"
    FLAG = "FLAG"
    BLOCK = "BLOCK"


class RuleMatch(BaseModel):
    rule_id: str
    severity: int
    category: str
    matched_text: str
    description: str


class SimilarityResult(BaseModel):
    top_match: str | None = None
    similarity_score: float = 0.0
    category: str | None = None
    risk_level: str = "low"


class LLMJudgeResult(BaseModel):
    malicious: bool = False
    confidence: float = 0.0
    category: str = "unknown"
    reasoning: str = ""


class HeuristicResult(BaseModel):
    score: int = 0
    findings: list[str] = Field(default_factory=list)


class LayerBreakdown(BaseModel):
    layer: str
    score: int
    details: dict = Field(default_factory=dict)


class DetectionResult(BaseModel):
    risk_score: int
    decision: DetectionDecision
    layer_breakdown: list[LayerBreakdown]
    reasoning_summary: str
    categories: list[str] = Field(default_factory=list)
    canary_triggered: bool = False
