"""
Pydantic Schemas for Patient Service Request/Response Validation
"""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import date, datetime
from uuid import UUID


# ============ Request Schemas ============

class PatientCreate(BaseModel):
    """Schema for creating a new patient"""
    full_name: str = Field(..., min_length=1, max_length=255, description="Patient's full name")
    dob: date = Field(..., description="Date of birth (YYYY-MM-DD)")
    gender: str = Field(..., min_length=1, max_length=50, description="Gender (e.g., Male, Female, Other)")
    diabetes_status: bool = Field(default=False, description="Whether patient has diabetes")


class PatientUpdate(BaseModel):
    """Schema for updating patient information"""
    full_name: Optional[str] = Field(None, min_length=1, max_length=255)
    dob: Optional[date] = None
    gender: Optional[str] = Field(None, min_length=1, max_length=50)
    diabetes_status: Optional[bool] = None


# ============ Response Schemas ============

class PatientResponse(BaseModel):
    """Schema for patient data in responses"""
    id: UUID
    full_name: str
    dob: date
    gender: str
    diabetes_status: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True  # Enables ORM mode for SQLAlchemy models


class PatientListResponse(BaseModel):
    """Schema for paginated patient list response"""
    total: int
    patients: list[PatientResponse]
