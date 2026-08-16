"""Layer 2 — embedding similarity via sentence-transformers + ChromaDB."""

from app.core.config import settings
from app.features.detection.schemas import SimilarityResult
from app.features.logging_audit.logger import get_logger

logger = get_logger("gatekeeper.detection.embedding")

_COLLECTION_NAME = "jailbreak_corpus"
_MODEL_NAME = "all-MiniLM-L6-v2"


class EmbeddingSimilarityChecker:
  def __init__(self) -> None:
    self._model = None
    self._collection = None
    self._initialized = False

  def _ensure_initialized(self) -> None:
    if self._initialized:
      return

    try:
      from sentence_transformers import SentenceTransformer
      import chromadb

      self._model = SentenceTransformer(_MODEL_NAME)
      client = chromadb.HttpClient(
        host=settings.CHROMA_HOST,
        port=settings.CHROMA_PORT,
      )
      self._collection = client.get_or_create_collection(
        name=_COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
      )
      self._initialized = True
      logger.info("embedding_similarity_initialized")
    except Exception as exc:
      logger.warning(
        "embedding_similarity_init_failed",
        extra={"error": str(exc)},
      )
      self._initialized = True

  async def check_similarity(self, prompt: str) -> SimilarityResult:
    self._ensure_initialized()

    if self._model is None or self._collection is None:
      return SimilarityResult(
        top_match=None,
        similarity_score=0.0,
        category=None,
        risk_level="low",
      )

    if self._collection.count() == 0:
      return SimilarityResult(
        top_match=None,
        similarity_score=0.0,
        category=None,
        risk_level="low",
      )

    try:
      embedding = self._model.encode(prompt).tolist()
      results = self._collection.query(
        query_embeddings=[embedding],
        n_results=1,
        include=["documents", "metadatas", "distances"],
      )

      if not results["documents"] or not results["documents"][0]:
        return SimilarityResult()

      top_match = results["documents"][0][0]
      distance = results["distances"][0][0]
      similarity = 1.0 - distance

      metadata = results["metadatas"][0][0] if results["metadatas"] else {}
      category = metadata.get("category", "unknown")

      risk_level = _score_to_risk_level(similarity)

      return SimilarityResult(
        top_match=top_match,
        similarity_score=round(similarity, 4),
        category=category,
        risk_level=risk_level,
      )
    except Exception as exc:
      logger.warning("embedding_similarity_check_failed", extra={"error": str(exc)})
      return SimilarityResult()

  def close(self) -> None:
    self._model = None
    self._collection = None
    self._initialized = False


def _score_to_risk_level(similarity: float) -> str:
  if similarity > settings.DETECTION_EMBEDDING_THRESHOLD_HIGH:
    return "high"
  if similarity > settings.DETECTION_EMBEDDING_THRESHOLD_MEDIUM:
    return "medium"
  return "low"


_checker: EmbeddingSimilarityChecker | None = None


def get_embedding_checker() -> EmbeddingSimilarityChecker:
  global _checker
  if _checker is None:
    _checker = EmbeddingSimilarityChecker()
  return _checker


async def check_similarity(prompt: str) -> SimilarityResult:
  return await get_embedding_checker().check_similarity(prompt)
