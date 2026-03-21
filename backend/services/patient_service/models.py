"""Database models for patient service."""

from sqlalchemy import Boolean, Column, Date, DateTime, ForeignKey, Integer, String, UniqueConstraint
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


class PatientAccess(Base):
    """Patient-level access control mapping.

    Grants a user access to a patient record. This enables object-level authorization
    without embedding user identifiers into the patient table.
    """

    __tablename__ = "patient_access"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    access_level = Column(String(50), nullable=False, default="owner")

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    __table_args__ = (
        UniqueConstraint("patient_id", "user_id", name="uq_patient_access_patient_user"),
    )


class PatientConsent(Base):
    """Consent audit records per patient (append-only semantics enforced at API layer)."""

    __tablename__ = "patient_consents"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.id", ondelete="CASCADE"), nullable=False, index=True)
    consent_type = Column(String(100), nullable=False, index=True)
    consent_given = Column(Boolean, nullable=False, default=True)
    consent_method = Column(String(50), nullable=False, default="digital_form")
    clinician_user_id = Column(Integer, nullable=True, index=True)
    ethics_approval_id = Column(String(100), nullable=True)
    duration_months = Column(Integer, nullable=False, default=12)

    recorded_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    valid_until = Column(DateTime(timezone=True), nullable=True, index=True)
