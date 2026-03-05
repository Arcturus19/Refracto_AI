"""
Database Models for Patient Service
"""

from sqlalchemy import Column, String, Boolean, Date, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from database import Base
import uuid


class Patient(Base):
    """
    Patient model for storing patient records
    """
    __tablename__ = "patients"
    
    # Primary Key - UUID
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    
    # Patient Information
    full_name = Column(String(255), nullable=False, index=True)
    dob = Column(Date, nullable=False)
    gender = Column(String(50), nullable=False)
    diabetes_status = Column(Boolean, default=False, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    def __repr__(self):
        return f"<Patient(id={self.id}, name='{self.full_name}', dob='{self.dob}')>"
