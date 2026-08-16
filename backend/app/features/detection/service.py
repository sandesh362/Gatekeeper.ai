"""Detection orchestration — runs all layers and aggregates results."""

import asyncio

from app.core.config import settings
from app.features.detection.aggregator import aggregate_risk
from app.features.detection.embedding_similarity.checker import check_similarity
from app.features.detection.llm_judge.judge import judge_prompt
from app.features.detection.rules_engine.checker import check_rules
from app.features.detection.schemas import (
    DetectionDecision,
    DetectionResult,
    LLMJudgeResult,
    SimilarityResult,
)
from app.features.detection.structural_heuristics.checker import check_heuristics
from app.features.logging_audit.logger import get_logger

logger = get_logger("gatekeeper.detection")


class DetectionService:
    async def analyze_prompt(self, prompt: str) -> DetectionResult:
        rule_matches = check_rules(prompt)
        heuristics = check_heuristics(prompt)

        async_tasks: list = [check_similarity(prompt)]
        if settings.DETECTION_LLM_JUDGE_ENABLED:
            async_tasks.append(judge_prompt(prompt))

        async_results = await asyncio.gather(*async_tasks, return_exceptions=True)

        similarity = async_results[0]
        if isinstance(similarity, BaseException):
            logger.warning("embedding_layer_failed", extra={"error": str(similarity)})
            similarity = SimilarityResult()

        if settings.DETECTION_LLM_JUDGE_ENABLED:
            judge_result = async_results[1]
            if isinstance(judge_result, BaseException):
                logger.warning("llm_judge_layer_failed", extra={"error": str(judge_result)})
                judge = LLMJudgeResult(
                    malicious=False,
                    confidence=0.5,
                    category="unknown",
                    reasoning=f"Judge layer error: {judge_result}",
                )
            else:
                judge = judge_result
        else:
            judge = LLMJudgeResult(
                malicious=False,
                confidence=0.0,
                category="disabled",
                reasoning="LLM judge disabled via config",
            )

        result = aggregate_risk(rule_matches, similarity, judge, heuristics)

        logger.info(
            "detection_completed",
            extra={
                "risk_score": result.risk_score,
                "decision": result.decision.value,
                "categories": result.categories,
            },
        )
        return result

    def apply_canary_block(self, result: DetectionResult) -> DetectionResult:
        """Override result to BLOCK when canary leakage is confirmed."""
        result.canary_triggered = True
        result.decision = DetectionDecision.BLOCK
        result.risk_score = 100
        result.reasoning_summary = (
            "CRITICAL: Canary token detected in response — confirmed system prompt leakage"
        )
        result.categories = list(set(result.categories + ["exfil"]))
        return result


detection_service = DetectionService()
