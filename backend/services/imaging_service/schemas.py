"""
Pydantic Schemas for Imaging Service
"""

from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from uuid import UUID
from models import ImageType


# ============ Response Schemas ============

class ImageUploadResponse(BaseModel):
    """Schema for image upload response"""
    id: int
    patient_id: UUID
    image_type: ImageType
    file_path: str
    file_name: str
    file_size: int
    content_type: str
    uploaded_at: datetime
    message: str = "Image uploaded successfully"
    
    class Config:
        from_attributes = True


class ImageRecordResponse(BaseModel):
    """Schema for image record with accessible URL"""
    id: int
    patient_id: UUID
    image_type: ImageType
    file_path: str
    file_name: str
    file_size: int
    content_type: str
    uploaded_at: datetime
    url: Optional[str] = None  # Presigned URL for accessing the image
    
    class Config:
        from_attributes = True


class ImageListResponse(BaseModel):
    """Schema for list of images"""
    total: int
    images: list[ImageRecordResponse]


class UploadStatsResponse(BaseModel):
    """Schema for upload statistics"""
    total_images: int
    total_size_bytes: int
    total_size_mb: float
    by_type: dict[str, int]
