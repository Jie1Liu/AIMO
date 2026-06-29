from __future__ import annotations
from typing import Optional
from functools import lru_cache

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_env: str = Field(default="development", alias="APP_ENV")
    database_url: str = Field(
        default="postgresql+psycopg://aimo:aimo@localhost:5432/aimo",
        alias="DATABASE_URL",
    )
    cors_origins_raw: str = Field(
        default="http://localhost:3000,http://127.0.0.1:3000",
        alias="CORS_ORIGINS",
    )

    aws_region: str = Field(default="us-east-1", alias="AWS_REGION")
    sqs_search_queue_url: Optional[str] = Field(default=None, alias="SQS_SEARCH_QUEUE_URL")
    sqs_ai_queue_url: Optional[str] = Field(default=None, alias="SQS_AI_QUEUE_URL")
    sqs_insight_queue_url: Optional[str] = Field(default=None, alias="SQS_INSIGHT_QUEUE_URL")
    sqs_outreach_queue_url: Optional[str] = Field(default=None, alias="SQS_OUTREACH_QUEUE_URL")
    secrets_manager_prefix: str = Field(default="aimo/", alias="SECRETS_MANAGER_PREFIX")

    bedrock_model_id: Optional[str] = Field(default=None, alias="BEDROCK_MODEL_ID")
    openai_api_key: Optional[str] = Field(default=None, alias="OPENAI_API_KEY")
    reddit_client_id: Optional[str] = Field(default=None, alias="REDDIT_CLIENT_ID")
    reddit_client_secret: Optional[str] = Field(default=None, alias="REDDIT_CLIENT_SECRET")
    youtube_client_id: Optional[str] = Field(default=None, alias="YOUTUBE_CLIENT_ID")
    youtube_client_secret: Optional[str] = Field(default=None, alias="YOUTUBE_CLIENT_SECRET")
    bluesky_service_url: str = Field(default="https://bsky.social", alias="BLUESKY_SERVICE_URL")
    jwt_secret: str = Field(default="change-me-in-production", alias="JWT_SECRET")

    mock_search_limit: int = 3
    lead_min_score: int = 40

    model_config = SettingsConfigDict(
        env_file=(".env", "../.env"),
        env_file_encoding="utf-8",
        extra="ignore",
        populate_by_name=True,
    )

    @field_validator("database_url")
    @classmethod
    def normalize_database_url(cls, value: str) -> str:
        if value.startswith("postgres://"):
            return value.replace("postgres://", "postgresql+psycopg://", 1)
        if value.startswith("postgresql://"):
            return value.replace("postgresql://", "postgresql+psycopg://", 1)
        return value

    @property
    def cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins_raw.split(",") if origin.strip()]

    @property
    def is_production(self) -> bool:
        return self.app_env.lower() == "production"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
