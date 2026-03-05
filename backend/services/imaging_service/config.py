"""
Configuration Settings for Imaging Service
"""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # Database Configuration
    DATABASE_URL: str
    
    # MinIO Configuration
    MINIO_ENDPOINT: str = "minio:9000"
    MINIO_ROOT_USER: str = "admin"
    MINIO_ROOT_PASSWORD: str = "password123"
    MINIO_SECURE: bool = False
    MINIO_BUCKET: str = "eye-scans"
    
    # Application Configuration
    APP_NAME: str = "Refracto AI - Imaging Service"
    VERSION: str = "1.0.0"
    DEBUG: bool = True
    
    # File Upload Settings
    MAX_FILE_SIZE: int = 100 * 1024 * 1024  # 100MB
    ALLOWED_IMAGE_TYPES: list = ["image/jpeg", "image/png", "image/tiff", "image/bmp"]
    ALLOWED_DICOM_TYPES: list = ["application/dicom"]
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# Global settings instance
settings = Settings()
