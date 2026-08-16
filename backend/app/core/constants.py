"""Shared application constants."""

API_V1_PREFIX = "/api/v1"

DEFAULT_PAGE_SIZE = 20
MAX_PAGE_SIZE = 100

# Detection layer identifiers (Phase 2+)
DETECTION_LAYER_RULES = "rules_engine"
DETECTION_LAYER_EMBEDDING = "embedding_similarity"
DETECTION_LAYER_LLM_JUDGE = "llm_judge"
DETECTION_LAYER_CANARY = "canary_tokens"
DETECTION_LAYER_HEURISTICS = "structural_heuristics"
