"""
Patient Service - FastAPI Application
Main entry point for the patient management microservice
"""

from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone
from fastapi import FastAPI, Depends, HTTPException, Query, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import Optional
from uuid import UUID

# Import local modules
from auth import require_authenticated_user
from config import settings
from database import engine, get_db, Base
from models import Patient, PatientAccess, PatientConsent
from schemas import (
    AccessGrantRequest,
    ConsentCreate,
    ConsentResponse,
    ConsentVerifyResponse,
    PatientCreate,
    PatientResponse,
    PatientUpdate,
)


def _is_internal_user(current_user: dict) -> bool:
    return current_user.get("auth_type") == "internal"


def _is_admin_user(current_user: dict) -> bool:
    return current_user.get("role") == "admin"


def _require_user_id(current_user: dict) -> int:
    user_id = current_user.get("user_id")
    if user_id is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing user identity")
    try:
        return int(user_id)
    except (TypeError, ValueError) as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid user identity") from exc


def _require_patient_access(db: Session, patient_id: UUID, current_user: dict) -> None:
    if _is_internal_user(current_user) or _is_admin_user(current_user):
        return

    user_id = _require_user_id(current_user)
    has_access = (
        db.query(PatientAccess)
        .filter(PatientAccess.patient_id == patient_id, PatientAccess.user_id == user_id)
        .first()
    )

    if not has_access:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized for this patient")


def _compute_valid_until(duration_months: int) -> datetime:
    # Conservative approximation: 30 days/month to avoid extra dependency.
    return datetime.now(timezone.utc) + timedelta(days=duration_months * 30)


def _cors_origins() -> list[str]:
    return [origin.strip() for origin in settings.CORS_ORIGINS.split(",") if origin.strip()]


# ============ Database Initialization ============

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan event handler for startup and shutdown.
    Creates database tables on startup.
    """
    # Startup: Create tables
    print("🔧 Creating patient database tables...")
    Base.metadata.create_all(bind=engine)
    print("✅ Patient database tables created successfully!")
    
    yield
    
    # Shutdown: Clean up resources
    print("👋 Shutting down patient service...")


# ============ FastAPI Application ============

app = FastAPI(
    title="Refracto AI - Patient Service",
    description="Patient Management Service for Refracto AI Medical Imaging Platform",
    version="1.0.0",
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
    lifespan=lifespan
)

# CORS middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============ Root & Health Endpoints ============

@app.get("/")
async def root():
    """Root endpoint - Health check and welcome message"""
    return {
        "message": "Refracto AI - Patient Service 🏥",
        "service": "patient_service",
        "status": "running",
        "version": "1.0.0",
        "endpoints": {
            "docs": "/docs",
            "patients": "/patients",
            "create_patient": "/patients (POST)",
            "get_patient": "/patients/{id} (GET)"
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring"""
    return {
        "status": "healthy",
        "service": "patient_service",
        "database": "connected"
    }


# ============ Patient Management Endpoints ============

@app.post("/patients", response_model=PatientResponse, status_code=status.HTTP_201_CREATED)
async def create_patient(
    patient_data: PatientCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_authenticated_user)
):
    """
    Create a new patient record.
    
    - **full_name**: Patient's full name (required)
    - **dob**: Date of birth in YYYY-MM-DD format (required)
    - **gender**: Gender (e.g., Male, Female, Other) (required)
    - **diabetes_status**: Whether patient has diabetes (default: false)
    """
    # Create new patient
    new_patient = Patient(
        full_name=patient_data.full_name,
        dob=patient_data.dob,
        gender=patient_data.gender,
        diabetes_status=patient_data.diabetes_status
    )
    
    db.add(new_patient)
    db.commit()
    db.refresh(new_patient)

    # Grant creator access (unless internal request)
    if not _is_internal_user(current_user):
        user_id = _require_user_id(current_user)
        db.add(PatientAccess(patient_id=new_patient.id, user_id=user_id, access_level="owner"))
        db.commit()
    
    return new_patient


@app.get("/patients", response_model=list[PatientResponse])
async def list_patients(
    search: Optional[str] = Query(None, description="Search by patient name"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=100, description="Maximum number of records to return"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_authenticated_user)
):
    """
    List all patients with optional search filtering.
    
    - **search**: Filter patients by name (case-insensitive partial match)
    - **skip**: Number of records to skip (pagination)
    - **limit**: Maximum number of records to return (max 100)
    """
    query = db.query(Patient)

    # Object-level filtering for non-admin users
    if not (_is_internal_user(current_user) or _is_admin_user(current_user)):
        user_id = _require_user_id(current_user)
        query = (
            query.join(PatientAccess, PatientAccess.patient_id == Patient.id)
            .filter(PatientAccess.user_id == user_id)
        )
    
    # Apply search filter if provided
    if search:
        search = search.strip()
        if len(search) < 2:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Search term must be at least 2 characters long"
            )
        search_term = f"%{search}%"
        query = query.filter(Patient.full_name.ilike(search_term))
    
    # Apply pagination and get results
    patients = query.offset(skip).limit(limit).all()
    
    return patients


@app.get("/patients/{patient_id}", response_model=PatientResponse)
async def get_patient(
    patient_id: UUID,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_authenticated_user)
):
    """
    Get details of a single patient by ID.
    
    - **patient_id**: UUID of the patient
    """
    _require_patient_access(db, patient_id, current_user)

    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Patient with ID {patient_id} not found"
        )
    
    return patient


@app.put("/patients/{patient_id}", response_model=PatientResponse)
async def update_patient(
    patient_id: UUID,
    patient_data: PatientUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_authenticated_user)
):
    """
    Update patient information.
    
    - **patient_id**: UUID of the patient to update
    - Only provided fields will be updated
    """
    _require_patient_access(db, patient_id, current_user)

    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Patient with ID {patient_id} not found"
        )
    
    # Update only provided fields
    update_data = patient_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(patient, field, value)
    
    db.commit()
    db.refresh(patient)
    
    return patient


@app.delete("/patients/{patient_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_patient(
    patient_id: UUID,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_authenticated_user)
):
    """
    Delete a patient record.
    
    - **patient_id**: UUID of the patient to delete
    """
    _require_patient_access(db, patient_id, current_user)

    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Patient with ID {patient_id} not found"
        )
    
    db.delete(patient)
    db.commit()
    
    return None


# ============ Statistics Endpoint ============

@app.get("/patients/stats/summary")
async def get_patient_statistics(
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_authenticated_user)
):
    """
    Get summary statistics about patients.
    """
    query = db.query(Patient)
    if not (_is_internal_user(current_user) or _is_admin_user(current_user)):
        user_id = _require_user_id(current_user)
        query = query.join(PatientAccess, PatientAccess.patient_id == Patient.id).filter(PatientAccess.user_id == user_id)

    total_patients = query.count()
    diabetes_patients = query.filter(Patient.diabetes_status == True).count()
    
    return {
        "total_patients": total_patients,
        "diabetes_patients": diabetes_patients,
        "non_diabetes_patients": total_patients - diabetes_patients,
        "diabetes_percentage": round((diabetes_patients / total_patients * 100), 2) if total_patients > 0 else 0
    }


# ============ Patient Access Control Endpoints ============


@app.post("/patients/{patient_id}/access/grant", status_code=status.HTTP_201_CREATED)
async def grant_patient_access(
    patient_id: UUID,
    grant: AccessGrantRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_authenticated_user),
):
    """Grant a user access to a patient. Admin-only."""
    if not (_is_internal_user(current_user) or _is_admin_user(current_user)):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin role required")

    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Patient with ID {patient_id} not found")

    existing = (
        db.query(PatientAccess)
        .filter(PatientAccess.patient_id == patient_id, PatientAccess.user_id == grant.user_id)
        .first()
    )
    if existing:
        existing.access_level = grant.access_level
    else:
        db.add(PatientAccess(patient_id=patient_id, user_id=grant.user_id, access_level=grant.access_level))

    db.commit()
    return {"status": "granted", "patient_id": str(patient_id), "user_id": grant.user_id, "access_level": grant.access_level}


# ============ Patient Consent Endpoints ============


@app.post("/patients/{patient_id}/consents", response_model=ConsentResponse, status_code=status.HTTP_201_CREATED)
async def record_patient_consent(
    patient_id: UUID,
    consent: ConsentCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_authenticated_user),
):
    """Record a consent event for a patient (append-only)."""
    _require_patient_access(db, patient_id, current_user)

    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Patient with ID {patient_id} not found")

    clinician_user_id = None if _is_internal_user(current_user) else _require_user_id(current_user)
    valid_until = _compute_valid_until(consent.duration_months)

    record = PatientConsent(
        patient_id=patient_id,
        consent_type=consent.consent_type,
        consent_given=consent.consent_given,
        consent_method=consent.consent_method,
        clinician_user_id=clinician_user_id,
        ethics_approval_id=consent.ethics_approval_id,
        duration_months=consent.duration_months,
        valid_until=valid_until,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


@app.get("/patients/{patient_id}/consents", response_model=list[ConsentResponse])
async def list_patient_consents(
    patient_id: UUID,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_authenticated_user),
):
    """List consent records for a patient."""
    _require_patient_access(db, patient_id, current_user)

    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Patient with ID {patient_id} not found")

    return (
        db.query(PatientConsent)
        .filter(PatientConsent.patient_id == patient_id)
        .order_by(PatientConsent.recorded_at.desc())
        .all()
    )


@app.get("/patients/{patient_id}/consents/verify", response_model=ConsentVerifyResponse)
async def verify_patient_consent(
    patient_id: UUID,
    consent_type: str = Query(..., min_length=1, max_length=100),
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_authenticated_user),
):
    """Verify whether the patient has active consent for the given type."""
    _require_patient_access(db, patient_id, current_user)

    now = datetime.now(timezone.utc)
    record = (
        db.query(PatientConsent)
        .filter(
            PatientConsent.patient_id == patient_id,
            PatientConsent.consent_type == consent_type,
            PatientConsent.consent_given == True,
        )
        .order_by(PatientConsent.recorded_at.desc())
        .first()
    )

    is_valid = bool(record and record.valid_until and record.valid_until >= now)
    return {
        "patient_id": patient_id,
        "consent_type": consent_type,
        "is_valid": is_valid,
        "valid_until": record.valid_until if record else None,
    }


# ============ Internal Service Verification Endpoint ============


@app.get("/internal/patients/{patient_id}/verify")
async def internal_verify_patient(
    patient_id: UUID,
    user_id: int | None = Query(None, ge=1),
    role: str | None = Query(None),
    consent_type: str | None = Query(None, min_length=1, max_length=100),
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_authenticated_user),
):
    """Internal-only verification for other services.

    Requires `X-Internal-Token`.
    Returns access decision and (optional) consent validity.
    """
    if not _is_internal_user(current_user):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Internal token required")

    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Patient with ID {patient_id} not found")

    allowed = False
    if role == "admin":
        allowed = True
    elif user_id is not None:
        allowed = bool(
            db.query(PatientAccess)
            .filter(PatientAccess.patient_id == patient_id, PatientAccess.user_id == user_id)
            .first()
        )

    consent_valid = None
    if consent_type:
        now = datetime.now(timezone.utc)
        record = (
            db.query(PatientConsent)
            .filter(
                PatientConsent.patient_id == patient_id,
                PatientConsent.consent_type == consent_type,
                PatientConsent.consent_given == True,
            )
            .order_by(PatientConsent.recorded_at.desc())
            .first()
        )
        consent_valid = bool(record and record.valid_until and record.valid_until >= now)

    return {"allowed": allowed, "consent_valid": consent_valid}


@app.get("/internal/users/{user_id}/patients")
async def internal_list_accessible_patients(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_authenticated_user),
):
    """Internal-only: list patient IDs a user can access.

    Requires `X-Internal-Token`.
    """
    if not _is_internal_user(current_user):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Internal token required")

    rows = db.query(PatientAccess.patient_id).filter(PatientAccess.user_id == user_id).all()
    return {"patient_ids": [str(r[0]) for r in rows]}


# ============ Development Server ============

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
