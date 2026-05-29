from pathlib import Path
from functools import lru_cache
from typing import Literal

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=("infra/env/.env", ".env"),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app_name: str = "CommerceOps AI API"
    app_version: str = "0.1.0"
    app_env: Literal["development", "test", "staging", "production"] = "development"
    api_prefix: str = "/api/v1"
    secret_key: str = Field(default="local-dev-secret", alias="SECRET_KEY")
    access_token_expiry_seconds: int = 3600
    refresh_cookie_name: str = "commerceops_refresh_token"
    refresh_cookie_secure: bool = False
    refresh_cookie_samesite: Literal["lax", "strict", "none"] = "lax"
    public_app_url: str | None = None
    cors_allowed_origins: str | None = Field(default=None, alias="CORS_ALLOWED_ORIGINS")

    database_url: str = Field(alias="DATABASE_URL")
    redis_url: str = Field(default="redis://redis:6379/0", alias="REDIS_URL")
    celery_broker_url: str | None = Field(default=None, alias="CELERY_BROKER_URL")
    celery_result_backend: str | None = Field(default=None, alias="CELERY_RESULT_BACKEND")
    secret_store_root: str = Field(default=str(Path.home() / ".commerceops_ai" / "secrets"), alias="SECRET_STORE_ROOT")
    low_inventory_threshold: int = Field(default=5, alias="LOW_INVENTORY_THRESHOLD")

    supabase_url: str = Field(alias="SUPABASE_URL")
    supabase_anon_key: str = Field(alias="SUPABASE_ANON_KEY")
    supabase_service_role_key: str = Field(alias="SUPABASE_SERVICE_ROLE_KEY")
    supabase_jwt_secret: str | None = Field(default=None, alias="SUPABASE_JWT_SECRET")

    shopify_api_key: str | None = Field(default=None, alias="SHOPIFY_API_KEY")
    shopify_api_secret: str | None = Field(default=None, alias="SHOPIFY_API_SECRET")
    shopify_app_url: str | None = Field(default=None, alias="SHOPIFY_APP_URL")
    shopify_redirect_url: str | None = Field(default=None, alias="SHOPIFY_REDIRECT_URL")
    shopify_scopes: str = Field(
        default="read_products,write_products,read_inventory,read_orders,read_customers,read_locations",
        alias="SHOPIFY_SCOPES",
    )
    shopify_api_version: str = Field(default="2026-04", alias="SHOPIFY_API_VERSION")

    llm_provider: str = Field(default="groq", alias="LLM_PROVIDER")
    llm_api_key: str | None = Field(default=None, alias="LLM_API_KEY")
    llm_model: str = Field(default="llama-3.3-70b-versatile", alias="LLM_MODEL")
    llm_base_url: str = Field(default="https://api.groq.com/openai/v1", alias="LLM_BASE_URL")
    embedding_api_key: str | None = Field(default=None, alias="EMBEDDING_API_KEY")
    embedding_base_url: str | None = Field(default=None, alias="EMBEDDING_BASE_URL")
    embedding_model: str = Field(default="text-embedding-3-small", alias="EMBEDDING_MODEL")
    rag_chunk_size: int = Field(default=800, alias="RAG_CHUNK_SIZE")
    rag_chunk_overlap: int = Field(default=120, alias="RAG_CHUNK_OVERLAP")
    rag_retrieval_top_k: int = Field(default=4, alias="RAG_RETRIEVAL_TOP_K")
    rag_max_prompt_chunks: int = Field(default=4, alias="RAG_MAX_PROMPT_CHUNKS")
    support_policy_confidence_threshold: float = Field(default=0.75, alias="SUPPORT_POLICY_CONFIDENCE_THRESHOLD")

    log_level: str = Field(default="INFO", alias="LOG_LEVEL")

    @property
    def resolved_celery_broker_url(self) -> str:
        return self.celery_broker_url or self.redis_url

    @property
    def resolved_celery_result_backend(self) -> str:
        return self.celery_result_backend or self.redis_url

    @property
    def resolved_cors_allowed_origins(self) -> list[str]:
        origins: list[str] = []
        if self.cors_allowed_origins:
            origins.extend(
                origin.strip()
                for origin in self.cors_allowed_origins.split(",")
                if origin.strip()
            )
        elif self.public_app_url:
            origins.append(self.public_app_url.rstrip("/"))

        if self.app_env == "development":
            for dev_origin in ("http://localhost:5173", "http://127.0.0.1:5173"):
                if dev_origin not in origins:
                    origins.append(dev_origin)

        return origins

    @model_validator(mode="after")
    def validate_required_runtime_settings(self) -> "Settings":
        required_values = {
            "DATABASE_URL": self.database_url,
            "SUPABASE_URL": self.supabase_url,
            "SUPABASE_ANON_KEY": self.supabase_anon_key,
            "SUPABASE_SERVICE_ROLE_KEY": self.supabase_service_role_key,
        }
        missing = [name for name, value in required_values.items() if not value or not str(value).strip()]
        if missing:
            joined = ", ".join(missing)
            raise ValueError(f"Missing required runtime settings: {joined}")
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
