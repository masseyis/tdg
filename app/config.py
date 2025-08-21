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
    max_cases_per_endpoint: int = 100
    default_cases_per_endpoint: int = 10
    request_timeout: int = 30
    
    # AI Provider settings (optional)
    openai_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    
    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()