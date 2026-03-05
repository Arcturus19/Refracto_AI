"""
Configuration Settings for ML Service
"""

from pydantic_settings import BaseSettings
import os


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # Model Configuration
    MODEL_PATH: str = "/app/models"
    
    # Application Configuration
    APP_NAME: str = "Refracto AI - ML Service"
    VERSION: str = "1.0.0"
    DEBUG: bool = True
    
    # Model Settings
    DEVICE: str = "cpu"  # Can be "cuda" if GPU available
    BATCH_SIZE: int = 1
    MAX_IMAGE_SIZE: int = 512  # Max dimension for input images
    
    # Model Names
    FUNDUS_MODEL_NAME: str = "efficientnet_b0"
    OCT_MODEL_NAME: str = "vit_base_patch16_224"
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# Global settings instance
settings = Settings()
