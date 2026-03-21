"""
Imaging Service - FastAPI Application
Main entry point for the medical imaging microservice
"""

import io
import logging
import uuid
from contextlib import asynccontextmanager
from datetime import datetime
from fastapi import FastAPI, Depends, File, HTTPException, UploadFile, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID
import anyio
import json
import urllib.error
import urllib.parse
import urllib.request

# Import local modules
from auth import require_authenticated_user
from database import engine, get_db, Base
from models import ImageRecord, ImageType
from schemas import ImageUploadResponse, ImageRecordResponse, ImageListResponse, UploadStatsResponse
from minio_handler import get_minio_handler
from config import settings
import pydicom
import numpy as np
from PIL import Image


logger = logging.getLogger(__name__)


def _is_internal_user(current_user: dict) -> bool:
    return current_user.get("auth_type") == "internal"


def _is_admin_user(current_user: dict) -> bool:
    return current_user.get("role") == "admin"


async def _verify_patient_access(patient_id: UUID, current_user: dict) -> None:
    mode = (settings.ACCESS_ENFORCEMENT_MODE or "required").strip().lower()
    if mode == "off":
        return

    # Internal ingestion worker is allowed.
    if _is_internal_user(current_user) or _is_admin_user(current_user):
        return

    base_url = settings.PATIENT_SERVICE_URL.rstrip("/")
    url = f"{base_url}/internal/patients/{patient_id}/verify"
    query = urllib.parse.urlencode(
        {
            "user_id": current_user.get("user_id"),
            "role": current_user.get("role"),
        },
        doseq=True,
    )
    full_url = f"{url}?{query}"

    headers = {}
    if settings.INTERNAL_API_TOKEN:
        headers["X-Internal-Token"] = settings.INTERNAL_API_TOKEN

    def _do_request() -> dict:
        req = urllib.request.Request(full_url, headers=headers, method="GET")
        with urllib.request.urlopen(req, timeout=5) as resp:
            body = resp.read().decode("utf-8")
            return json.loads(body) if body else {}

    try:
        data = await anyio.to_thread.run_sync(_do_request)
    except urllib.error.HTTPError as http_err:
        if http_err.code == 404:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Patient not found") from http_err
        if http_err.code == 403:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Patient verification forbidden") from http_err
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Patient verification failed") from http_err
    except Exception as exc:
        logger.error("Patient verification call failed: %s", exc)
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Patient verification unavailable") from exc

    if not data.get("allowed", False):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized for this patient")


async def _get_accessible_patient_ids(current_user: dict) -> list[UUID]:
    if _is_internal_user(current_user) or _is_admin_user(current_user):
        return []

    user_id = current_user.get("user_id")
    if user_id is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing user identity")

    base_url = settings.PATIENT_SERVICE_URL.rstrip("/")
    url = f"{base_url}/internal/users/{user_id}/patients"

    headers = {}
    if settings.INTERNAL_API_TOKEN:
        headers["X-Internal-Token"] = settings.INTERNAL_API_TOKEN

    def _do_request() -> dict:
        req = urllib.request.Request(url, headers=headers, method="GET")
        with urllib.request.urlopen(req, timeout=5) as resp:
            body = resp.read().decode("utf-8")
            return json.loads(body) if body else {}

    try:
        data = await anyio.to_thread.run_sync(_do_request)
    except urllib.error.HTTPError as http_err:
        if http_err.code == 403:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Patient listing forbidden") from http_err
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Patient listing failed") from http_err
    except Exception as exc:
        logger.error("Patient listing call failed: %s", exc)
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Patient listing unavailable") from exc

    patient_ids = data.get("patient_ids") or []
    parsed: list[UUID] = []
    for pid in patient_ids:
        try:
            parsed.append(UUID(str(pid)))
        except Exception:
            continue

    return parsed


def _cors_origins() -> list[str]:
    return [origin.strip() for origin in settings.CORS_ORIGINS.split(",") if origin.strip()]


# ============ Database Initialization ============

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan event handler for startup and shutdown.
    Creates database tables and initializes MinIO on startup.
    """
    # Startup: Create tables and initialize MinIO
    logger.info("🔧 Creating imaging database tables...")
    Base.metadata.create_all(bind=engine)
    logger.info("✅ Imaging database tables created successfully!")
    
    # Initialize MinIO handler (will create bucket if it doesn't exist)
    logger.info("🔧 Initializing MinIO connection...")
    minio = get_minio_handler()
    logger.info("✅ MinIO initialized successfully!")
    
    yield
    
    # Shutdown: Clean up resources
    logger.info("👋 Shutting down imaging service...")


# ============ FastAPI Application ============

app = FastAPI(
    title="Refracto AI - Imaging Service",
    description="Medical Image Storage and Retrieval Service for Refracto AI Platform",
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


# ============ Helper Functions ============

def validate_file_type(file: UploadFile) -> tuple[bool, str, ImageType]:
    """
    Validate if file is an allowed image or DICOM file
    
    Returns:
        (is_valid, error_message, image_type)
    """
    content_type = file.content_type or ""
    
    # Check for standard images
    if content_type in settings.ALLOWED_IMAGE_TYPES:
        # Default to FUNDUS, can be overridden later
        return True, "", ImageType.FUNDUS
    
    # Check for DICOM
    if content_type in settings.ALLOWED_DICOM_TYPES:
        return True, "", ImageType.OCT
    
    # Check by file extension as fallback
    filename = file.filename or ""
    ext = filename.lower().split('.')[-1] if '.' in filename else ""
    
    if ext in ['jpg', 'jpeg', 'png', 'tiff', 'tif', 'bmp']:
        return True, "", ImageType.FUNDUS
    
    if ext in ['dcm', 'dicom']:
        return True, "", ImageType.OCT
    
    return False, f"Unsupported file type: {content_type}. Allowed: images (JPEG, PNG, TIFF, BMP) and DICOM files.", ImageType.FUNDUS


def validate_file_content(file_content: bytes, image_type: ImageType) -> None:
    if not file_content:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file is empty"
        )

    try:
        if image_type == ImageType.OCT:
            pydicom.dcmread(io.BytesIO(file_content), stop_before_pixels=True)
        else:
            image = Image.open(io.BytesIO(file_content))
            image.verify()
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file content is not a valid supported medical image"
        ) from exc


# ============ Root & Health Endpoints ============

@app.get("/")
async def root():
    """Root endpoint - Health check and welcome message"""
    return {
        "message": "Refracto AI - Imaging Service 📸",
        "service": "imaging_service",
        "status": "running",
        "version": "1.0.0",
        "endpoints": {
            "docs": "/docs",
            "upload": "/upload/{patient_id}",
            "images": "/images/{patient_id}",
            "stats": "/stats"
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring"""
    minio = get_minio_handler()
    bucket_exists = minio.client.bucket_exists(settings.MINIO_BUCKET)
    
    return {
        "status": "healthy",
        "service": "imaging_service",
        "database": "connected",
        "minio": "connected" if bucket_exists else "bucket_missing"
    }


# ============ Image Upload Endpoint ============

@app.post("/upload/{patient_id}", response_model=ImageUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_image(
    patient_id: UUID,
    file: UploadFile = File(...),
    image_type: ImageType | None = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_authenticated_user)
):
    """
    Upload a medical image for a patient
    
    **Step A**: Validate if it's an image or DICOM  
    **Step B**: Upload binary data to MinIO bucket 'eye-scans'  
    **Step C**: Save metadata to Postgres
    
    Args:
        patient_id: UUID of the patient
        file: Image or DICOM file to upload
        image_type: Type of image (FUNDUS or OCT)
        
    Returns:
        ImageUploadResponse with upload details
    """
    await _verify_patient_access(patient_id, current_user)

    # Step A: Validate file type
    is_valid, error_msg, detected_type = validate_file_type(file)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_msg
        )
    
    # Use provided image_type or detected type
    final_image_type = image_type or detected_type
    
    try:
        # Read file content
        file_content = await file.read()
        file_size = len(file_content)
        
        # Check file size
        if file_size > settings.MAX_FILE_SIZE:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"File too large. Maximum size: {settings.MAX_FILE_SIZE / (1024*1024)}MB"
            )

        validate_file_content(file_content, final_image_type)
        
        # Generate unique file path in MinIO
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_extension = file.filename.split('.')[-1] if '.' in file.filename else 'bin'
        unique_id = str(uuid.uuid4())[:8]
        object_name = f"patients/{patient_id}/{final_image_type.value.lower()}/{timestamp}_{unique_id}.{file_extension}"
        
        # Step B: Upload to MinIO
        minio = get_minio_handler()
        
        # === NEW: DICOM Conversion Logic ===
        final_file_content = file_content
        final_content_type = file.content_type
        final_file_extension = file_extension
        final_file_name = file.filename or f"upload_{unique_id}.{file_extension}"
        
        if file_extension in ['dcm', 'dicom'] or final_image_type == ImageType.OCT:
            try:
                logger.info(f"Converting DICOM to PNG for {file.filename}")
                # Read DICOM using pydicom
                dicom_data = pydicom.dcmread(io.BytesIO(file_content))
                
                # Extract pixel array
                if hasattr(dicom_data, 'pixel_array'):
                    img_array = dicom_data.pixel_array
                    
                    # Normalize if needed (e.g., 16-bit to 8-bit)
                    if img_array.dtype != np.uint8:
                        # Rescale to 0-255
                        min_val = np.min(img_array)
                        max_val = np.max(img_array)
                        if max_val > min_val:
                            img_array = ((img_array - min_val) / (max_val - min_val) * 255.0).astype(np.uint8)
                        else:
                            img_array = np.zeros_like(img_array, dtype=np.uint8)
                    
                    # Ensure it's 2D or 3D
                    if len(img_array.shape) > 2 and img_array.shape[2] not in [1, 3, 4]:
                        # Handle multi-frame by just taking the first frame
                        if len(img_array.shape) == 3:
                            img_array = img_array[0]
                        elif len(img_array.shape) == 4:
                            img_array = img_array[0, :, :, :3]
                            
                    image = Image.fromarray(img_array)
                    
                    # Convert to PNG byte stream
                    png_io = io.BytesIO()
                    image.save(png_io, format='PNG')
                    final_file_content = png_io.getvalue()
                    
                    # Update metadata for storage
                    final_content_type = 'image/png'
                    final_file_extension = 'png'
                    final_file_name = f"{file.filename.rsplit('.', 1)[0]}.png"
                    file_size = len(final_file_content)
                    
                    # Update object_name
                    object_name = f"patients/{patient_id}/{final_image_type.value.lower()}/{timestamp}_{unique_id}.png"
                    logger.info(f"DICOM successfully converted to {file_size} bytes PNG.")
                else:
                    logger.warning("DICOM has no pixel_array, skipping conversion.")
            except Exception as dicom_err:
                logger.error(f"DICOM conversion failed: {dicom_err}")
                # Fall back to original file if conversion fails
                pass
        # === END DICOM Conversion ===

        upload_success = minio.upload_file(
            file_data=final_file_content,
            bucket_name=settings.MINIO_BUCKET,
            object_name=object_name,
            content_type=final_content_type
        )
        
        if not upload_success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to upload image to storage"
            )
        
        # Step C: Save metadata to database
        image_record = ImageRecord(
            patient_id=patient_id,
            image_type=final_image_type,
            file_path=object_name,
            file_name=final_file_name,
            file_size=file_size,
            content_type=final_content_type or "application/octet-stream"
        )
        
        db.add(image_record)
        db.commit()
        db.refresh(image_record)
        
        logger.info(f"✓ Image uploaded successfully: {object_name} (Patient: {patient_id})")
        
        return ImageUploadResponse(
            **image_record.__dict__,
            message=f"Image uploaded successfully to {settings.MINIO_BUCKET}"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"✗ Upload error: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Upload failed due to an internal server error"
        )


# ============ Image Retrieval Endpoints ============

@app.get("/images/recent", response_model=List[ImageRecordResponse])
async def get_recent_images(
    limit: int = 10,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_authenticated_user)
):
    """
    Get recent images across all patients (for dashboard/notifications)
    
    Args:
        limit: Maximum number of images to return (default: 10)
        
    Returns:
        List of recent image records with presigned URLs
    """
    try:
        query = db.query(ImageRecord).order_by(ImageRecord.uploaded_at.desc())

        if not (_is_internal_user(current_user) or _is_admin_user(current_user)):
            allowed_patient_ids = await _get_accessible_patient_ids(current_user)
            if not allowed_patient_ids:
                return []
            query = query.filter(ImageRecord.patient_id.in_(allowed_patient_ids))

        # Get recent images ordered by upload time
        images = query.limit(limit).all()
        
        # Generate presigned URLs
        processed_images = []
        minio_handler = get_minio_handler() # Initialize minio_handler here
        for img in images:
            presigned_url = minio_handler.get_file_url(
                bucket_name=settings.MINIO_BUCKET,
                object_name=img.file_path
            )
            
            processed_images.append(
                ImageRecordResponse(
                    id=img.id,
                    patient_id=img.patient_id,
                    image_type=img.image_type.value,
                    file_name=img.file_name,
                    file_size=img.file_size,
                    content_type=img.content_type,
                    uploaded_at=img.uploaded_at,
                    url=presigned_url # Changed from image_url to url to match ImageRecordResponse
                )
            )
        
        logger.info(f"Retrieved {len(processed_images)} recent images")
        return processed_images
        
    except Exception as e:
        logger.error(f"Error fetching recent images: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch recent images"
        )


@app.get("/images/{patient_id}", response_model=ImageListResponse)
async def get_patient_images(
    patient_id: UUID,
    image_type: ImageType = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_authenticated_user)
):
    """
    Get all images for a patient with presigned URLs
    
    Args:
        patient_id: UUID of the patient
        image_type: Optional filter by image type (FUNDUS or OCT)
        
    Returns:
        List of image records with accessible URLs
    """
    await _verify_patient_access(patient_id, current_user)

    # Query database for patient's images
    query = db.query(ImageRecord).filter(ImageRecord.patient_id == patient_id)
    
    if image_type:
        query = query.filter(ImageRecord.image_type == image_type)
    
    images = query.order_by(ImageRecord.uploaded_at.desc()).all()
    
    # Generate presigned URLs for each image
    minio = get_minio_handler()
    image_responses = []
    
    for img in images:
        url = minio.get_file_url(
            bucket_name=settings.MINIO_BUCKET,
            object_name=img.file_path,
            expires_seconds=3600  # 1 hour
        )
        
        image_response = ImageRecordResponse(
            **img.__dict__,
            url=url
        )
        image_responses.append(image_response)
    
    return ImageListResponse(
        total=len(image_responses),
        images=image_responses
    )


@app.get("/image/{image_id}", response_model=ImageRecordResponse)
async def get_image_by_id(
    image_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_authenticated_user)
):
    """
    Get a specific image by ID with presigned URL
    
    Args:
        image_id: ID of the image record
        
    Returns:
        Image record with accessible URL
    """
    image = db.query(ImageRecord).filter(ImageRecord.id == image_id).first()
    
    if not image:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Image with ID {image_id} not found"
        )

    await _verify_patient_access(image.patient_id, current_user)
    
    # Generate presigned URL
    minio = get_minio_handler()
    url = minio.get_file_url(
        bucket_name=settings.MINIO_BUCKET,
        object_name=image.file_path,
        expires_seconds=3600
    )
    
    return ImageRecordResponse(
        **image.__dict__,
        url=url
    )


# ============ Statistics Endpoint ============

@app.get("/stats", response_model=UploadStatsResponse)
async def get_upload_statistics(
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_authenticated_user)
):
    """
    Get upload statistics across all patients
    
    Returns:
        Statistics about uploaded images
    """
    base_query = db.query(ImageRecord)
    if not (_is_internal_user(current_user) or _is_admin_user(current_user)):
        allowed_patient_ids = await _get_accessible_patient_ids(current_user)
        if not allowed_patient_ids:
            return UploadStatsResponse(
                total_images=0,
                total_size_bytes=0,
                total_size_mb=0,
                by_type={"FUNDUS": 0, "OCT": 0},
            )
        base_query = base_query.filter(ImageRecord.patient_id.in_(allowed_patient_ids))

    total_images = base_query.count()
    total_size = base_query.with_entities(func.sum(ImageRecord.file_size)).scalar() or 0

    # Count by type
    fundus_count = base_query.filter(ImageRecord.image_type == ImageType.FUNDUS).count()
    oct_count = base_query.filter(ImageRecord.image_type == ImageType.OCT).count()
    
    return UploadStatsResponse(
        total_images=total_images,
        total_size_bytes=total_size,
        total_size_mb=round(total_size / (1024 * 1024), 2),
        by_type={
            "FUNDUS": fundus_count,
            "OCT": oct_count
        }
    )


# ============ Delete Endpoint ============

@app.delete("/image/{image_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_image(
    image_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_authenticated_user)
):
    """
    Delete an image record and its file from storage
    
    Args:
        image_id: ID of the image to delete
    """
    image = db.query(ImageRecord).filter(ImageRecord.id == image_id).first()
    
    if not image:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Image with ID {image_id} not found"
        )

    await _verify_patient_access(image.patient_id, current_user)
    
    # Delete from MinIO
    minio = get_minio_handler()
    minio.delete_file(
        bucket_name=settings.MINIO_BUCKET,
        object_name=image.file_path
    )
    
    # Delete from database
    db.delete(image)
    db.commit()
    
    logger.info(f"✓ Image deleted: {image.file_path}")
    
    return None


# Add missing import
from sqlalchemy import func


# ============ Development Server ============

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_level="info"
    )
