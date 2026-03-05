"""
Patient Service - FastAPI Application
Main entry point for the patient management microservice
"""

from fastapi import FastAPI, Depends, HTTPException, status, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from contextlib import asynccontextmanager
from typing import Optional
from uuid import UUID

# Import local modules
from database import engine, get_db, Base
from models import Patient
from schemas import PatientCreate, PatientUpdate, PatientResponse, PatientListResponse


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
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# CORS middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Update this with specific origins in production
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
async def create_patient(patient_data: PatientCreate, db: Session = Depends(get_db)):
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
    
    return new_patient


@app.get("/patients", response_model=list[PatientResponse])
async def list_patients(
    search: Optional[str] = Query(None, description="Search by patient name"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=100, description="Maximum number of records to return"),
    db: Session = Depends(get_db)
):
    """
    List all patients with optional search filtering.
    
    - **search**: Filter patients by name (case-insensitive partial match)
    - **skip**: Number of records to skip (pagination)
    - **limit**: Maximum number of records to return (max 100)
    """
    query = db.query(Patient)
    
    # Apply search filter if provided
    if search:
        search_term = f"%{search}%"
        query = query.filter(Patient.full_name.ilike(search_term))
    
    # Apply pagination and get results
    patients = query.offset(skip).limit(limit).all()
    
    return patients


@app.get("/patients/{patient_id}", response_model=PatientResponse)
async def get_patient(patient_id: UUID, db: Session = Depends(get_db)):
    """
    Get details of a single patient by ID.
    
    - **patient_id**: UUID of the patient
    """
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
    db: Session = Depends(get_db)
):
    """
    Update patient information.
    
    - **patient_id**: UUID of the patient to update
    - Only provided fields will be updated
    """
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
async def delete_patient(patient_id: UUID, db: Session = Depends(get_db)):
    """
    Delete a patient record.
    
    - **patient_id**: UUID of the patient to delete
    """
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
async def get_patient_statistics(db: Session = Depends(get_db)):
    """
    Get summary statistics about patients.
    """
    total_patients = db.query(Patient).count()
    diabetes_patients = db.query(Patient).filter(Patient.diabetes_status == True).count()
    
    return {
        "total_patients": total_patients,
        "diabetes_patients": diabetes_patients,
        "non_diabetes_patients": total_patients - diabetes_patients,
        "diabetes_percentage": round((diabetes_patients / total_patients * 100), 2) if total_patients > 0 else 0
    }


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
