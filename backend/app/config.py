"""Configuration management for AgentVerse using pydantic-settings."""

import os
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    # Project metadata
    PROJECT_NAME: str = "AgentVerse"
    VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"
    LOG_LEVEL: str = "INFO"

    # OpenAI Configuration
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_MODEL: str = "gpt-4o-mini"
    OPENAI_TEMPERATURE: float = 0.2

    # Search Provider Configuration
    # Options: "auto", "tavily", "duckduckgo", "mock"
    SEARCH_PROVIDER: str = "auto"
    TAVILY_API_KEY: Optional[str] = None

    # Database Configuration
    # Defaults to local SQLite if not configured or if PostgreSQL is unavailable
    DATABASE_URL: str = "sqlite:///./agentverse.db"

    # Server Configuration
    BACKEND_HOST: str = "0.0.0.0"
    BACKEND_PORT: int = 8000
    STREAMLIT_PORT: int = 8501

    # Multi-Agent Workflow Parameters
    MAX_RESEARCH_ITERATIONS: int = 2
    MAX_SOURCES_PER_TOPIC: int = 5
    REQUEST_TIMEOUT: int = 30
    DEFAULT_DEPTH: str = "standard"  # quick, standard, deep

    @property
    def is_openai_configured(self) -> bool:
        """Check if a valid OpenAI API key is present."""
        return bool(self.OPENAI_API_KEY and self.OPENAI_API_KEY.strip() and not self.OPENAI_API_KEY.startswith("your_"))

    @property
    def is_tavily_configured(self) -> bool:
        """Check if a valid Tavily API key is present."""
        return bool(self.TAVILY_API_KEY and self.TAVILY_API_KEY.strip() and not self.TAVILY_API_KEY.startswith("your_"))

    @property
    def effective_search_provider(self) -> str:
        """Determine active search provider based on keys and settings."""
        if self.SEARCH_PROVIDER == "tavily" and self.is_tavily_configured:
            return "tavily"
        if self.SEARCH_PROVIDER == "auto":
            if self.is_tavily_configured:
                return "tavily"
            return "duckduckgo"
        if self.SEARCH_PROVIDER in ("duckduckgo", "mock"):
            return self.SEARCH_PROVIDER
        return "duckduckgo"


settings = Settings()
