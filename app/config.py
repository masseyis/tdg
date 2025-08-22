"""Application configuration"""
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
    openai_model: str = "gpt-3.5-turbo"  # Options: gpt-4o-mini (fastest), gpt-3.5-turbo (balanced), gpt-4o (best quality)
    anthropic_model: str = "claude-3-haiku-20240307"  # Options: claude-3-haiku-20240307 (fastest), claude-3-sonnet-20240229 (balanced), claude-3-opus-20240229 (best quality)
    
    # AI Generation settings
    ai_temperature: float = 0.7  # Lower = more consistent, faster
    ai_max_tokens: int = 2000  # Lower = faster generation
    ai_timeout: int = 15  # Shorter timeout for faster fallback
    
    # Concurrency settings
    ai_concurrency_limit: int = 10  # Maximum concurrent AI requests
    max_concurrent_requests: int = 50  # Maximum concurrent HTTP requests


    class Config:
        env_file = ".env"
        case_sensitive = False

settings = Settings()
