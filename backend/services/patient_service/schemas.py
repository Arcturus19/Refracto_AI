"""Pydantic schemas for patient service request/response validation."""

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


# ============ Consent Schemas ============


class ConsentCreate(BaseModel):
    """Schema for recording a consent event for a patient."""

    consent_type: str = Field(..., min_length=1, max_length=100, description="Type of consent (e.g., ml_analysis)")
    consent_given: bool = Field(default=True, description="Whether consent was given")
    consent_method: str = Field(default="digital_form", min_length=1, max_length=50)
    ethics_approval_id: Optional[str] = Field(default=None, max_length=100)
    duration_months: int = Field(default=12, ge=1, le=120)


class ConsentResponse(BaseModel):
    id: int
    patient_id: UUID
    consent_type: str
    consent_given: bool
    consent_method: str
    clinician_user_id: Optional[int] = None
    ethics_approval_id: Optional[str] = None
    duration_months: int
    recorded_at: datetime
    valid_until: Optional[datetime] = None

    class Config:
        from_attributes = True


class ConsentVerifyResponse(BaseModel):
    patient_id: UUID
    consent_type: str
    is_valid: bool
    valid_until: Optional[datetime] = None


# ============ Access Control Schemas ============


class AccessGrantRequest(BaseModel):
    """Schema for granting a user access to a patient (admin-only)."""

    user_id: int = Field(..., ge=1)
    access_level: str = Field(default="viewer", min_length=1, max_length=50)
