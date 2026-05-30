from functools import lru_cache

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    database_url: str
    jwt_secret: SecretStr
    jwt_lifetime_seconds: int = 3600

    OPENAI_API_KEY: str
    EMBEDDING_MODEL: str = "text-embedding-3-small"
    EMBEDDING_ENCODING: str = "cl100k_base"
    CHUNK_SIZE: int = 800
    CHUNK_OVERLAP: int = 120
    LLM_MODEL: str = "gpt-4o-mini"
    LLM_MODEL_MINI: str = "gpt-4o-mini"
    QUERY_TOP_K: int = 5
    OPENAI_API_KEY: str

    LOGFIRE_ENABLED: bool = True
    LOGFIRE_TOKEN: SecretStr | None = None
    LOGFIRE_SERVICE_NAME: str = "smart-pot-backend"
    LOGFIRE_ENVIRONMENT: str = "dev"


@lru_cache
def get_settings() -> Settings:
    return Settings()
