"""
Database Models for Imaging Service
"""

from sqlalchemy import Column, Integer, String, DateTime, Enum, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from database import Base
import enum


class ImageType(str, enum.Enum):
    """Image type enumeration"""
    FUNDUS = "FUNDUS"
    OCT = "OCT"


class ImageRecord(Base):
    """
    ImageRecord model for tracking uploaded medical images
    """
    __tablename__ = "image_records"
    
    # Primary Key
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    
    # Patient Reference (foreign key to patients table)
    patient_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    
    # Image Information
    image_type = Column(Enum(ImageType), nullable=False)
    file_path = Column(String(500), nullable=False)  # MinIO object path
    file_name = Column(String(255), nullable=False)
    file_size = Column(Integer, nullable=False)  # Size in bytes
    content_type = Column(String(100), nullable=False)
    
    # Timestamps
    uploaded_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    def __repr__(self):
        return f"<ImageRecord(id={self.id}, patient_id='{self.patient_id}', type='{self.image_type}')>"
