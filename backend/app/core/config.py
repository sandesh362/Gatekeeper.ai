"""Application settings loaded from environment variables."""

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    APP_NAME: str = "gatekeeper"
    APP_ENV: str = "development"
    DEBUG: bool = True
    LOG_LEVEL: str = "INFO"

    HOST: str = "0.0.0.0"
    PORT: int = 8000

    DATABASE_URL: str = "postgresql+asyncpg://gatekeeper:gatekeeper@localhost:5432/gatekeeper"
    SECRET_KEY: str = "change-me-in-production"

    OPENAI_API_KEY: str = ""
    ANTHROPIC_API_KEY: str = ""

    # Stored as comma-separated string to avoid pydantic-settings JSON parsing issues.
    CORS_ORIGINS: str = "http://localhost:5173,http://localhost:3000"

    CHROMA_HOST: str = "localhost"
    CHROMA_PORT: int = 8001

    # Detection engine (Phase 3)
    DETECTION_LLM_JUDGE_ENABLED: bool = True
    DETECTION_LLM_JUDGE_PROVIDER: str = "anthropic"
    DETECTION_LLM_JUDGE_MODEL: str = "claude-3-haiku-20240307"
    DETECTION_OLLAMA_BASE_URL: str = "http://localhost:11434"
    DETECTION_OLLAMA_MODEL: str = "llama3.2"

    DETECTION_WEIGHT_RULES: float = 0.3
    DETECTION_WEIGHT_EMBEDDING: float = 0.25
    DETECTION_WEIGHT_LLM_JUDGE: float = 0.3
    DETECTION_WEIGHT_HEURISTICS: float = 0.15

    DETECTION_EMBEDDING_THRESHOLD_HIGH: float = 0.85
    DETECTION_EMBEDDING_THRESHOLD_MEDIUM: float = 0.7

    DETECTION_PASS_THRESHOLD: int = 40
    DETECTION_BLOCK_THRESHOLD: int = 75

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def ensure_async_driver(cls, value: str) -> str:
        if isinstance(value, str) and value.startswith("postgresql://"):
            return value.replace("postgresql://", "postgresql+asyncpg://", 1)
        return value

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]

    @property
    def detection_weights(self) -> dict[str, float]:
        return {
            "rules": self.DETECTION_WEIGHT_RULES,
            "embedding": self.DETECTION_WEIGHT_EMBEDDING,
            "llm_judge": self.DETECTION_WEIGHT_LLM_JUDGE,
            "heuristics": self.DETECTION_WEIGHT_HEURISTICS,
        }


settings = Settings()
