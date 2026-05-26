import os
from typing import Literal
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    """
    Application Settings loaded from environment variables and .env file.
    Uses Pydantic Settings v2 for validation and type-safety.
    """
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    # Application Configuration
    APP_NAME: str = "AI Knowledge Assistant"
    APP_ENV: Literal["development", "production", "testing"] = "development"
    DEBUG: bool = True
    PORT: int = 8000
    HOST: str = "0.0.0.0"

    # Logging Configuration
    LOG_LEVEL: str = "INFO"

    # OpenAI API Configuration
    OPENAI_API_KEY: str = Field(default="your-openai-api-key-here")
    OPENAI_MODEL_NAME: str = "gpt-4o"
    EMBEDDING_MODEL_NAME: str = "text-embedding-3-small"

    # ML Provider Configuration (local or openai)
    MODEL_PROVIDER: Literal["openai", "local"] = "local"

    # Storage Configuration
    UPLOAD_DIR: str = "./data/uploads"
    VECTOR_STORE_DIR: str = "./data/vectorstore"
    VECTOR_DB_TYPE: Literal["faiss", "chromadb"] = "faiss"

    @property
    def is_openai_key_configured(self) -> bool:
        """Helper to verify if a valid-looking OpenAI API Key is provided."""
        return (
            self.OPENAI_API_KEY != "your-openai-api-key-here"
            and len(self.OPENAI_API_KEY.strip()) > 0
        )

# Instantiate settings to be imported by other modules
settings = Settings()
