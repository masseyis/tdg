"""Application configuration"""

import os
from typing import Optional

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings"""

    # App settings
    app_secret: str = "change-me-in-production"
    port: int = 8080
    log_level: str = "INFO"
    max_workers: int = 4

    # Generation settings
    max_cases_per_endpoint: int = 500
    default_cases_per_endpoint: int = 10
    request_timeout: int = 30

    # AI Provider settings (optional)
    openai_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None

    # AI Model settings for speed/quality tradeoff
    openai_model: str = (
        "gpt-3.5-turbo"  # Options: gpt-4o-mini (fastest), gpt-3.5-turbo (balanced), gpt-4o (best quality)
    )
    anthropic_model: str = (
        "claude-3-haiku-20240307"  # Options: claude-3-haiku-20240307 (fastest), claude-3-sonnet-20240229 (balanced), claude-3-opus-20240229 (best quality)
    )

    # AI Generation settings
    ai_temperature: float = 0.7  # Lower = more consistent, faster
    ai_max_tokens: int = 2000  # Lower = faster generation
    ai_timeout: int = 60  # Increased timeout for better reliability

    # Concurrency settings (optimized for performance and memory stability)
    ai_concurrency_limit: int = 8  # Maximum concurrent AI requests
    max_concurrent_requests: int = 30  # Maximum concurrent HTTP requests

    # Uvicorn server settings
    uvicorn_workers: int = int(
        os.getenv("UVICORN_WORKERS", "2")
    )  # Number of uvicorn worker processes
    uvicorn_threads: int = int(os.getenv("UVICORN_THREADS", "4"))  # Number of threads per worker

    # Generation service settings
    generation_workers: int = int(
        os.getenv("GENERATION_WORKERS", "2")
    )  # Number of generation worker threads
    generation_queue_size: int = int(
        os.getenv("GENERATION_QUEUE_SIZE", "100")
    )  # Maximum queued generation requests

    # Sentry settings
    sentry_dsn: Optional[str] = None
    sentry_environment: str = "development"
    sentry_traces_sample_rate: float = 0.1
    sentry_profiles_sample_rate: float = 0.1

    # Clerk authentication settings
    clerk_jwt_public_key: Optional[str] = None
    clerk_issuer: str = "https://clerk.your-domain.com"
    clerk_secret_key: Optional[str] = None
    clerk_webhook_secret: Optional[str] = None

    # Development settings
    disable_auth_for_dev: bool = os.getenv("DISABLE_AUTH_FOR_DEV", "false").lower() == "true"

    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
