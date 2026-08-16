"""Risk aggregator — combines all detection layer outputs into a single score."""

from app.core.config import settings
from app.core.constants import (
  DETECTION_LAYER_EMBEDDING,
  DETECTION_LAYER_HEURISTICS,
  DETECTION_LAYER_LLM_JUDGE,
  DETECTION_LAYER_RULES,
)
from app.features.detection.schemas import (
  DetectionDecision,
  DetectionResult,
  HeuristicResult,
  LayerBreakdown,
  LLMJudgeResult,
  RuleMatch,
  SimilarityResult,
)


def aggregate_risk(
  rule_matches: list[RuleMatch],
  similarity: SimilarityResult,
  judge: LLMJudgeResult,
  heuristics: HeuristicResult,
) -> DetectionResult:
  rules_score = _score_rules(rule_matches)
  embedding_score = _score_embedding(similarity)
  judge_score = _score_judge(judge)
  heuristics_score = heuristics.score

  weights = settings.detection_weights
  weighted = (
    rules_score * weights["rules"]
    + embedding_score * weights["embedding"]
    + judge_score * weights["llm_judge"]
    + heuristics_score * weights["heuristics"]
  )
  risk_score = min(int(round(weighted)), 100)

  # High-confidence rule matches floor the score so a single severe match can BLOCK.
  if rule_matches:
    risk_score = max(risk_score, rules_score)

  layer_breakdown = [
    LayerBreakdown(
      layer=DETECTION_LAYER_RULES,
      score=rules_score,
      details={
        "matches": [m.model_dump() for m in rule_matches],
        "match_count": len(rule_matches),
      },
    ),
    LayerBreakdown(
      layer=DETECTION_LAYER_EMBEDDING,
      score=embedding_score,
      details=similarity.model_dump(),
    ),
    LayerBreakdown(
      layer=DETECTION_LAYER_LLM_JUDGE,
      score=judge_score,
      details=judge.model_dump(),
    ),
    LayerBreakdown(
      layer=DETECTION_LAYER_HEURISTICS,
      score=heuristics_score,
      details=heuristics.model_dump(),
    ),
  ]

  categories = _collect_categories(rule_matches, similarity, judge)
  decision = _decide(risk_score)
  reasoning = _build_reasoning(rule_matches, similarity, judge, heuristics, risk_score, decision)

  return DetectionResult(
    risk_score=risk_score,
    decision=decision,
    layer_breakdown=layer_breakdown,
    reasoning_summary=reasoning,
    categories=categories,
  )


def _score_rules(matches: list[RuleMatch]) -> int:
  if not matches:
    return 0
  return max(m.severity for m in matches)


def _score_embedding(similarity: SimilarityResult) -> int:
  if similarity.risk_level == "high":
    return 90
  if similarity.risk_level == "medium":
    return 60
  if similarity.similarity_score > 0:
    return 15
  return 0


def _score_judge(judge: LLMJudgeResult) -> int:
  if judge.category == "disabled":
    return 0
  if judge.malicious:
    return min(int(judge.confidence * 100), 100)
  if judge.category == "unknown":
    return 50
  return max(int((1.0 - judge.confidence) * 20), 0)


def _decide(risk_score: int) -> DetectionDecision:
  if risk_score >= settings.DETECTION_BLOCK_THRESHOLD:
    return DetectionDecision.BLOCK
  if risk_score >= settings.DETECTION_PASS_THRESHOLD:
    return DetectionDecision.FLAG
  return DetectionDecision.PASS


def _collect_categories(
  rule_matches: list[RuleMatch],
  similarity: SimilarityResult,
  judge: LLMJudgeResult,
) -> list[str]:
  categories: set[str] = set()
  for match in rule_matches:
    categories.add(match.category)
  if similarity.category:
    categories.add(similarity.category)
  if judge.category and judge.category not in ("benign", "unknown", "disabled"):
    categories.add(judge.category)
  return sorted(categories)


def _build_reasoning(
  rule_matches: list[RuleMatch],
  similarity: SimilarityResult,
  judge: LLMJudgeResult,
  heuristics: HeuristicResult,
  risk_score: int,
  decision: DetectionDecision,
) -> str:
  parts: list[str] = [f"Risk score {risk_score}/100 → {decision.value}"]

  if rule_matches:
    top = max(rule_matches, key=lambda m: m.severity)
    parts.append(f"Rules: {len(rule_matches)} match(es), top={top.category} (severity {top.severity})")

  if similarity.risk_level != "low":
    parts.append(
      f"Embedding: {similarity.risk_level} similarity ({similarity.similarity_score:.2f})"
    )

  if judge.malicious:
    parts.append(f"LLM judge: malicious ({judge.category}, confidence {judge.confidence:.2f})")
  elif judge.category != "disabled":
    parts.append(f"LLM judge: benign (confidence {judge.confidence:.2f})")

  if heuristics.findings:
    parts.append(f"Heuristics: {len(heuristics.findings)} finding(s)")

  return "; ".join(parts)
