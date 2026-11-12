"""Application configuration loaded from environment variables / .env file."""

from functools import lru_cache
from pathlib import Path

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

_BACKEND_DIR = Path(__file__).resolve().parent


class Settings(BaseSettings):
    """Typed application settings (pydantic v2 BaseSettings).

    Values are read from the environment first, then from ``backend/.env``,
    then from the project-root ``.env``.
    """

    model_config = SettingsConfigDict(
        env_file=(_BACKEND_DIR.parent / ".env", _BACKEND_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # LLM
    groq_api_key: str = ""
    groq_model: str = "openai/gpt-oss-20b"  # llama3-8b-8192 was decommissioned by Groq

    # Redis cache
    redis_url: str = "redis://localhost:6379"
    cache_ttl_seconds: int = 3600

    # MySQL (SQLAlchemy URL; the async driver is applied in database.py)
    database_url: str = "mysql+pymysql://root:root@localhost:3306/ai_doc_assistant"

    # JWT
    jwt_secret: str = "change-me"
    jwt_algorithm: str = "HS256"
    jwt_expire_hours: int = 24

    # Server
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    cors_origins: list[str] = ["http://localhost:3000", "http://localhost:5173"]

    # Uploads / vector store
    max_upload_mb: int = 10
    chroma_dir: str = str(_BACKEND_DIR / "chroma_db")

    @field_validator("redis_url")
    @classmethod
    def _clean_redis_url(cls, value: str) -> str:
        """Accept a pasted ``redis-cli --tls -u <url>`` string and return a plain URL."""
        value = value.strip()
        if "redis-cli" in value:
            tls = "--tls" in value
            value = value.split("-u", 1)[-1].strip()
            if tls and value.startswith("redis://"):
                value = "rediss://" + value[len("redis://"):]
        return value


@lru_cache
def get_settings() -> Settings:
    """Return the cached Settings instance."""
    return Settings()


settings = get_settings()
