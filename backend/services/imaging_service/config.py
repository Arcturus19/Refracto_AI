"""
Configuration Settings for Imaging Service
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

    # Cross-service integration
    PATIENT_SERVICE_URL: str = "http://patient_service:8000"

    # Patient access enforcement
    # off | required
    ACCESS_ENFORCEMENT_MODE: str = "required"
    
    # MinIO Configuration
    MINIO_ENDPOINT: str = "minio:9000"
    MINIO_ROOT_USER: str
    MINIO_ROOT_PASSWORD: str
    MINIO_SECURE: bool = False
    MINIO_BUCKET: str = "eye-scans"
    
    # Application Configuration
    APP_NAME: str = "Refracto AI - Imaging Service"
    VERSION: str = "1.0.0"
    DEBUG: bool = False
    
    # File Upload Settings
    MAX_FILE_SIZE: int = 100 * 1024 * 1024  # 100MB
    ALLOWED_IMAGE_TYPES: list = ["image/jpeg", "image/png", "image/tiff", "image/bmp"]
    ALLOWED_DICOM_TYPES: list = ["application/dicom"]
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# Global settings instance
settings = Settings()
