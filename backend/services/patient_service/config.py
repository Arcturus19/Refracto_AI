"""
Configuration Settings for Patient Service
"""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # Database Configuration
    DATABASE_URL: str
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_COOKIE_NAME: str = "access_token"
    CORS_ORIGINS: str = "http://localhost:5173"
    INTERNAL_API_TOKEN: str | None = None
    
    # Application Configuration
    APP_NAME: str = "Refracto AI - Patient Service"
    VERSION: str = "1.0.0"
    DEBUG: bool = False
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# Global settings instance
settings = Settings()
