"""
Configuration Settings for ML Service
"""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # Model Configuration
    MODEL_PATH: str = "/app/models"
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_COOKIE_NAME: str = "access_token"
    CORS_ORIGINS: str = "http://localhost:5173"
    INTERNAL_API_TOKEN: str | None = None

    # Cross-service integration
    PATIENT_SERVICE_URL: str = "http://patient_service:8000"

    # Consent enforcement
    # off | if_patient_provided | required
    CONSENT_ENFORCEMENT_MODE: str = "if_patient_provided"
    CONSENT_TYPE: str = "ml_analysis"

    # Audit logging (tamper-evident hash chain)
    AUDIT_LOG_PATH: str = "/data/audit/ml_predictions_audit.jsonl"
    AUDIT_HASH_SALT: str = "refracto_ai_audit_salt_change_me"
    
    # Application Configuration
    APP_NAME: str = "Refracto AI - ML Service"
    VERSION: str = "1.0.0"
    DEBUG: bool = False
    
    # Model Settings
    DEVICE: str = "cpu"  # Can be "cuda" if GPU available
    BATCH_SIZE: int = 1
    MAX_IMAGE_SIZE: int = 512  # Max dimension for input images
    MAX_UPLOAD_SIZE_BYTES: int = 20 * 1024 * 1024
    
    # Model Names
    FUNDUS_MODEL_NAME: str = "efficientnet_b0"
    OCT_MODEL_NAME: str = "vit_base_patch16_224"
    OCT_CHECKPOINT_PATH: str | None = None
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"


# Global settings instance
settings = Settings()
