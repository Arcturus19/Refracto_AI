"""
ML Service - FastAPI Application
Machine Learning microservice for medical image analysis
"""

import io
import logging
import time
from contextlib import asynccontextmanager
from fastapi import Depends, FastAPI, File, Form, HTTPException, UploadFile, status
from fastapi.middleware.cors import CORSMiddleware
from PIL import Image
from torch.utils.data import DataLoader
from torchvision import transforms
from auth import require_authenticated_user
from config import settings
from core.tamper_evident_audit import TamperEvidentAuditLog
from core.model_loader import get_models, load_models_on_startup
from core.preprocessing import get_preprocessor
from core.xai_engine import get_explainer
from xai_api_routes import router as xai_router
from routes_p0_integration import router as p0_router
import numpy as np
import torch
from core.dataset_loader import RefractoDataset
import anyio
import hashlib
import requests


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


_audit_log = TamperEvidentAuditLog(settings.AUDIT_LOG_PATH)


def _hash_patient_id(patient_id: str) -> str:
    salted = f"{patient_id}{settings.AUDIT_HASH_SALT}".encode("utf-8")
    return hashlib.sha256(salted).hexdigest()


async def _verify_patient_access_and_consent(patient_id: str | None, current_user: dict) -> dict:
    mode = (settings.CONSENT_ENFORCEMENT_MODE or "off").strip().lower()
    if mode not in {"off", "if_patient_provided", "required"}:
        mode = "if_patient_provided"

    if mode == "off":
        return {"checked": False}

    if mode == "required" and not patient_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="patient_id is required")

    if mode == "if_patient_provided" and not patient_id:
        return {"checked": False}

    if not patient_id:
        return {"checked": False}

    url = f"{settings.PATIENT_SERVICE_URL.rstrip('/')}/internal/patients/{patient_id}/verify"
    params = {
        "user_id": current_user.get("user_id"),
        "role": current_user.get("role"),
        "consent_type": settings.CONSENT_TYPE,
    }
    headers = {}
    if settings.INTERNAL_API_TOKEN:
        headers["X-Internal-Token"] = settings.INTERNAL_API_TOKEN

    def _do_request() -> requests.Response:
        return requests.get(url, params=params, headers=headers, timeout=5)

    try:
        resp = await anyio.to_thread.run_sync(_do_request)
    except Exception as exc:
        logger.error("Patient verification call failed: %s", exc)
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Consent verification unavailable") from exc

    if resp.status_code == 404:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Patient not found")
    if resp.status_code == 403:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Patient verification forbidden")
    if resp.status_code != 200:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Consent verification failed")

    data = resp.json()
    if not data.get("allowed", False):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized for this patient")

    consent_valid = data.get("consent_valid")
    if consent_valid is False:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Patient consent not verified")

    return {"checked": True, "consent_valid": consent_valid}


def _cors_origins() -> list[str]:
    return [origin.strip() for origin in settings.CORS_ORIGINS.split(",") if origin.strip()]


def _models_loaded() -> bool:
    models = get_models()
    return bool(getattr(models, "_models_loaded", False))


async def _read_validated_upload(file: UploadFile) -> bytes:
    await file.seek(0)
    image_bytes = await file.read()

    if not image_bytes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file is empty"
        )

    if len(image_bytes) > settings.MAX_UPLOAD_SIZE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File too large. Maximum size is {settings.MAX_UPLOAD_SIZE_BYTES // (1024 * 1024)}MB"
        )

    try:
        image = Image.open(io.BytesIO(image_bytes))
        image.verify()
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file is not a valid image"
        ) from exc

    return image_bytes


# ============ Application Lifecycle ============

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan event handler for startup and shutdown.
    Loads ML models on startup.
    """
    # Startup: Load models
    logger.info("🔧 Initializing ML Service...")
    logger.info(f"📁 Model path: {settings.MODEL_PATH}")
    logger.info(f"🖥️  Device: {settings.DEVICE}")
    
    # Load models (this will download them if needed)
    success = load_models_on_startup()
    
    if success:
        model_info = get_models().get_model_info()
        oct_info = model_info.get("models", {}).get("oct", {})
        logger.info(
            "🔬 OCT runtime source=%s checkpoint=%s classes=%s",
            oct_info.get("source", "unknown"),
            oct_info.get("checkpoint_path", "none"),
            oct_info.get("classes", []),
        )
        logger.info("✅ ML Service initialized successfully!")
    else:
        logger.warning("⚠️  ML Service started but models failed to load")
    
    yield
    
    # Shutdown: Clean up resources
    logger.info("👋 Shutting down ML service...")



# ============ FastAPI Application ============

app = FastAPI(
    title="Refracto AI - ML Service",
    description="Machine Learning Service for Medical Image Analysis",
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

# Register XAI explainability routes
app.include_router(xai_router, dependencies=[Depends(require_authenticated_user)])

# Register Phase-1 P0 integration routes (used by integration tests)
app.include_router(p0_router)


# ============ Root & Health Endpoints ============

@app.get("/")
async def root():
    """Root endpoint - Health check and welcome message"""
    return {
        "message": "Refracto AI - ML Service 🤖",
        "service": "ml_service",
        "status": "running",
        "version": "1.0.0",
        "device": settings.DEVICE,
        "endpoints": {
            "docs": "/docs",
            "health": "/health",
            "analyze_fundus": "/analyze/fundus",
            "analyze_oct": "/analyze/oct",
            "predict": "/predict",
            "test_data_loading": "/test-data-loading",
            "xai_explain_dr": "/api/ml/xai/explain/dr",
            "xai_explain_glaucoma": "/api/ml/xai/explain/glaucoma",
            "xai_explain_refraction": "/api/ml/xai/explain/refraction",
            "xai_feature_importance": "/api/ml/xai/feature-importance/{task}",
            "xai_interpretation_guide": "/api/ml/xai/interpretation-guide"
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring"""
    return {
        "status": "healthy",
        "service": "ml_service",
        "device": settings.DEVICE,
        "models_loaded": _models_loaded()
    }


@app.get("/health/ready")
async def readiness_check():
    """Readiness check used by orchestrators."""
    models_loaded = _models_loaded()
    if not models_loaded:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Models are still loading"
        )

    return {
        "status": "ready",
        "service": "ml_service",
        "models_loaded": True,
    }


# ============ ML Prediction Endpoints ============

@app.post("/analyze/fundus")
async def analyze_fundus(
    file: UploadFile = File(...),
    patient_id: str | None = Form(default=None),
    current_user: dict = Depends(require_authenticated_user)
):
    """
    Analyze fundus image for diabetic retinopathy
    
    Returns DR severity classification with probabilities
    """
    start_time = time.time()
    
    try:
        verification = await _verify_patient_access_and_consent(patient_id, current_user)

        # Reset file pointer and read bytes safely
        image_bytes = await _read_validated_upload(file)
        
        # Get preprocessor and models
        preprocessor = get_preprocessor()
        models = get_models()
        
        # Preprocess image
        image_tensor = preprocessor.preprocess(image_bytes, task_type='fundus')
        
        # Run prediction
        result = models.predict(image_tensor, task_type='fundus')
        
        # Add metadata
        result['filename'] = file.filename
        result['processing_time_ms'] = round((time.time() - start_time) * 1000, 2)
        
        logger.info(f"✓ Fundus analysis: {result['prediction']['class']} (confidence: {result['prediction']['confidence']:.2f})")

        if patient_id:
            _audit_log.append(
                {
                    "event": "analyze_fundus",
                    "patient_hash": _hash_patient_id(patient_id),
                    "user_id": current_user.get("user_id"),
                    "role": current_user.get("role"),
                    "consent_verified": verification.get("consent_valid"),
                    "model": "fundus",
                    "prediction": result.get("prediction", {}).get("class"),
                    "confidence": result.get("prediction", {}).get("confidence"),
                }
            )
        
        return result
        
    except Exception as e:
        logger.error(f"✗ Fundus analysis error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Analysis failed due to an internal server error"
        )


@app.post("/analyze/oct")
async def analyze_oct(
    file: UploadFile = File(...),
    patient_id: str | None = Form(default=None),
    current_user: dict = Depends(require_authenticated_user)
):
    """
    Analyze OCT image for retinal conditions
    
    Returns OCT-based condition classification
    """
    start_time = time.time()
    
    try:
        verification = await _verify_patient_access_and_consent(patient_id, current_user)

        # Reset file pointer and read bytes safely
        image_bytes = await _read_validated_upload(file)
        
        # Get preprocessor and models
        preprocessor = get_preprocessor()
        models = get_models()
        
        # Preprocess image
        image_tensor = preprocessor.preprocess(image_bytes, task_type='oct')
        
        # Run prediction
        result = models.predict(image_tensor, task_type='oct')
        
        # Add metadata
        result['filename'] = file.filename
        result['processing_time_ms'] = round((time.time() - start_time) * 1000, 2)
        
        logger.info(f"✓ OCT analysis: {result['prediction']['class']} (confidence: {result['prediction']['confidence']:.2f})")

        if patient_id:
            _audit_log.append(
                {
                    "event": "analyze_oct",
                    "patient_hash": _hash_patient_id(patient_id),
                    "user_id": current_user.get("user_id"),
                    "role": current_user.get("role"),
                    "consent_verified": verification.get("consent_valid"),
                    "model": "oct",
                    "prediction": result.get("prediction", {}).get("class"),
                    "confidence": result.get("prediction", {}).get("confidence"),
                }
            )
        
        return result
        
    except Exception as e:
        logger.error(f"✗ OCT analysis error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Analysis failed due to an internal server error"
        )


@app.post("/analyze/refraction")
async def analyze_refraction(
    file: UploadFile = File(...),
    patient_id: str | None = Form(default=None),
    current_user: dict = Depends(require_authenticated_user)
):
    """
    Analyze fundus image for refraction measurements
    
    Returns predicted Sphere, Cylinder, and Axis values
    """
    start_time = time.time()
    
    try:
        verification = await _verify_patient_access_and_consent(patient_id, current_user)

        # Reset file pointer and read bytes safely
        image_bytes = await _read_validated_upload(file)
        
        # Get preprocessor and models
        preprocessor = get_preprocessor()
        models = get_models()
        
        # Preprocess image
        image_tensor = preprocessor.preprocess(image_bytes, task_type='refraction')
        
        # Run prediction
        result = models.predict(image_tensor, task_type='refraction')
        
        # Add metadata
        result['filename'] = file.filename
        result['processing_time_ms'] = round((time.time() - start_time) * 1000, 2)
        
        logger.info(f"✓ Refraction prediction: {result['prescription']}")

        if patient_id:
            _audit_log.append(
                {
                    "event": "analyze_refraction",
                    "patient_hash": _hash_patient_id(patient_id),
                    "user_id": current_user.get("user_id"),
                    "role": current_user.get("role"),
                    "consent_verified": verification.get("consent_valid"),
                    "model": "refraction",
                    "prediction": result.get("prescription"),
                    "confidence": result.get("confidence"),
                }
            )
        
        return result
        
    except Exception as e:
        logger.error(f"✗ Refraction analysis error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Analysis failed due to an internal server error"
        )


@app.post("/predict")
async def predict(
    file: UploadFile = File(...),
    image_type: str = "fundus",
    patient_id: str | None = Form(default=None),
    current_user: dict = Depends(require_authenticated_user)
):
    """
    General prediction endpoint
    
    Args:
        file: Image file to analyze
        image_type: Type of image ("fundus", "oct", or "refraction")
        
    Returns:
        Prediction results based on image type
    """
    valid_types = ["fundus", "oct", "refraction"]
    
    if image_type not in valid_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"image_type must be one of: {', '.join(valid_types)}"
        )
    
    start_time = time.time()
    
    try:
        verification = await _verify_patient_access_and_consent(patient_id, current_user)

        # Reset file pointer and read bytes safely
        image_bytes = await _read_validated_upload(file)
        
        # Get preprocessor and models
        preprocessor = get_preprocessor()
        models = get_models()
        
        # Preprocess image
        image_tensor = preprocessor.preprocess(image_bytes, task_type=image_type)
        
        # Run prediction
        result = models.predict(image_tensor, task_type=image_type)
        
        # Add metadata
        result['filename'] = file.filename
        result['processing_time_ms'] = round((time.time() - start_time) * 1000, 2)
        
        logger.info(f"✓ Prediction complete: {image_type}")

        if patient_id:
            _audit_log.append(
                {
                    "event": "predict",
                    "patient_hash": _hash_patient_id(patient_id),
                    "user_id": current_user.get("user_id"),
                    "role": current_user.get("role"),
                    "consent_verified": verification.get("consent_valid"),
                    "model": image_type,
                    "prediction": result.get("prediction", {}).get("class") or result.get("prescription"),
                    "confidence": result.get("prediction", {}).get("confidence") or result.get("confidence"),
                }
            )
        
        return result
        
    except Exception as e:
        logger.error(f"✗ Prediction error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Prediction failed due to an internal server error"
        )


# ============ Simplified Prediction Endpoints ============

@app.post("/predict/refraction")
async def predict_refraction(
    file: UploadFile = File(...),
    patient_id: str | None = Form(default=None),
    current_user: dict = Depends(require_authenticated_user)
):
    """
    Simplified refraction prediction endpoint
    
    Returns:
        JSON with sphere, cylinder, and axis values
        Example: { "sphere": -2.50, "cylinder": -0.75, "axis": 180 }
    """
    try:
        verification = await _verify_patient_access_and_consent(patient_id, current_user)

        # Reset file pointer and read bytes safely
        image_bytes = await _read_validated_upload(file)
        
        # Get preprocessor and models
        preprocessor = get_preprocessor()
        models = get_models()
        
        # Preprocess image
        image_tensor = preprocessor.preprocess(image_bytes, task_type='refraction')
        
        # Run prediction
        result = models.predict(image_tensor, task_type='refraction')
        
        # Extract measurements
        measurements = result['measurements']
        
        logger.info(f"✓ Refraction: SPH {measurements['sphere']:+.2f} CYL {measurements['cylinder']:.2f} × {measurements['axis']:.0f}°")

        if patient_id:
            _audit_log.append(
                {
                    "event": "predict_refraction",
                    "patient_hash": _hash_patient_id(patient_id),
                    "user_id": current_user.get("user_id"),
                    "role": current_user.get("role"),
                    "consent_verified": verification.get("consent_valid"),
                    "model": "refraction",
                    "prediction": measurements,
                    "confidence": result.get("confidence"),
                }
            )
        
        return {
            "sphere": measurements['sphere'],
            "cylinder": measurements['cylinder'],
            "axis": measurements['axis']
        }
        
    except Exception as e:
        logger.error(f"✗ Refraction prediction error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Prediction failed due to an internal server error"
        )


@app.post("/predict/pathology")
async def predict_pathology(
    file: UploadFile = File(...),
    patient_id: str | None = Form(default=None),
    current_user: dict = Depends(require_authenticated_user)
):
    """
    Simplified pathology prediction endpoint
    
    Runs fundus image through EfficientNet for DR grading and glaucoma risk
    
    Returns:
        JSON with DR grade and glaucoma risk
        Example: { "dr_grade": 2, "glaucoma_risk": 0.85 }
    """
    try:
        verification = await _verify_patient_access_and_consent(patient_id, current_user)

        # Reset file pointer and read bytes safely
        image_bytes = await _read_validated_upload(file)
        
        # Get preprocessor and models
        preprocessor = get_preprocessor()
        models = get_models()
        
        # Preprocess image
        image_tensor = preprocessor.preprocess(image_bytes, task_type='fundus')
        
        # Run prediction
        result = models.predict(image_tensor, task_type='fundus')
        
        # Extract DR grade
        dr_grade = result['prediction']['class_id']
        
        # Calculate glaucoma risk (mock calculation from severity score)
        # In production, this would use a dedicated glaucoma model
        severity = result['severity_score']
        glaucoma_risk = round(min(severity * 1.2, 1.0), 2)  # Scale and cap at 1.0
        
        logger.info(f"✓ Pathology: DR Grade {dr_grade}, Glaucoma Risk {glaucoma_risk:.2f}")

        if patient_id:
            _audit_log.append(
                {
                    "event": "predict_pathology",
                    "patient_hash": _hash_patient_id(patient_id),
                    "user_id": current_user.get("user_id"),
                    "role": current_user.get("role"),
                    "consent_verified": verification.get("consent_valid"),
                    "model": "fundus",
                    "prediction": {"dr_grade": dr_grade, "glaucoma_risk": glaucoma_risk},
                    "confidence": result.get("prediction", {}).get("confidence"),
                }
            )
        
        return {
            "dr_grade": dr_grade,
            "glaucoma_risk": glaucoma_risk,
            "disclaimer": "Glaucoma risk is an assistive heuristic and must not be used as a standalone clinical diagnosis."
        }
        
    except Exception as e:
        logger.error(f"✗ Pathology prediction error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Prediction failed due to an internal server error"
        )


# ============ Explainability Endpoints (XAI) ============

@app.post("/explain/pathology")
async def explain_pathology(
    file: UploadFile = File(...),
    patient_id: str | None = Form(default=None),
    current_user: dict = Depends(require_authenticated_user)
):
    """
    Explainable AI endpoint for pathology predictions
    
    Returns diagnosis with Grad-CAM heatmap showing which regions influenced the prediction
    
    Returns:
        JSON with diagnosis and base64-encoded heatmap
        Example: {
            "diagnosis": { "dr_grade": 2, "glaucoma_risk": 0.65 },
            "heatmap_base64": "data:image/png;base64,..."
        }
    """
    start_time = time.time()
    
    try:
        verification = await _verify_patient_access_and_consent(patient_id, current_user)

        # Reset file pointer and read bytes safely
        image_bytes = await _read_validated_upload(file)
        
        # Get preprocessor, models, and explainer
        preprocessor = get_preprocessor()
        models = get_models()
        explainer = get_explainer()
        
        # Step 1: Run normal prediction to get diagnosis
        logger.info("Step 1: Running prediction...")
        
        # Preprocess image
        image_tensor = preprocessor.preprocess(image_bytes, task_type='fundus')
        
        # Run prediction
        result = models.predict(image_tensor, task_type='fundus')
        
        # Extract DR grade
        dr_grade = result['prediction']['class_id']
        
        # Calculate glaucoma risk (from severity score)
        severity = result['severity_score']
        glaucoma_risk = round(min(severity * 1.2, 1.0), 2)
        
        diagnosis = {
            "dr_grade": dr_grade,
            "glaucoma_risk": glaucoma_risk,
            "dr_class": result['prediction']['class'],
            "confidence": result['prediction']['confidence']
        }
        
        logger.info(f"✓ Diagnosis: DR Grade {dr_grade}, Confidence {result['prediction']['confidence']:.2f}")
        
        # Step 2: Generate Grad-CAM heatmap
        logger.info("Step 2: Generating Grad-CAM heatmap...")
        
        # Prepare original image for overlay
        pil_image = Image.open(io.BytesIO(image_bytes)).convert('RGB')
        pil_image = pil_image.resize((224, 224))  # Resize to model input size
        original_image = np.array(pil_image) / 255.0  # Normalize to [0, 1]
        
        # Generate heatmap
        # Note: Running on CPU as specified for optimization
        _, heatmap_base64 = explainer.generate_heatmap(
            model=models.fundus_model,
            input_tensor=image_tensor,
            original_image=original_image,
            target_class=dr_grade,  # Target the predicted class
            use_cuda=False  # Force CPU for stability
        )
        
        processing_time = round((time.time() - start_time) * 1000, 2)
        
        logger.info(f"✓ Explanation generated (processing time: {processing_time}ms)")

        if patient_id:
            _audit_log.append(
                {
                    "event": "explain_pathology",
                    "patient_hash": _hash_patient_id(patient_id),
                    "user_id": current_user.get("user_id"),
                    "role": current_user.get("role"),
                    "consent_verified": verification.get("consent_valid"),
                    "model": "fundus",
                    "prediction": diagnosis,
                    "confidence": diagnosis.get("confidence"),
                }
            )
        
        return {
            "diagnosis": diagnosis,
            "heatmap_base64": heatmap_base64,
            "processing_time_ms": processing_time,
            "explanation": f"The highlighted regions show areas that most influenced the {result['prediction']['class']} diagnosis.",
            "disclaimer": "Explainability output is intended for clinician review and not as a standalone diagnosis."
        }
        
    except Exception as e:
        logger.error(f"✗ Explanation generation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Explanation generation failed due to an internal server error"
        )


# ============ Testing Endpoints ============

@app.get("/test-data-loading")
async def test_data_loading(current_user: dict = Depends(require_authenticated_user)):
    """
    Test endpoint for RefractoDataset and DataLoader
    
    Verifies that the dataset can be loaded and batched correctly
    
    Returns:
        JSON summary with batch shape and sample labels
    """
    if not settings.DEBUG:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Not found"
        )

    try:
        # Define simple transform
        transform = transforms.Compose([
            transforms.ToTensor()
        ])
        
        # Initialize RefractoDataset
        csv_path = "/data/processed/clean_labels.csv"
        image_dir = "/data/processed/train"
        
        logger.info(f"Attempting to load dataset from:")
        logger.info(f"  CSV: {csv_path}")
        logger.info(f"  Images: {image_dir}")
        
        dataset = RefractoDataset(
            csv_file=csv_path,
            img_dir=image_dir,
            transform=transform
        )
        
        logger.info(f"✓ Dataset initialized successfully with {len(dataset)} samples")
        
        # Create DataLoader with batch_size=4
        dataloader = DataLoader(
            dataset,
            batch_size=4,
            shuffle=False,
            num_workers=0  # Use 0 for Docker compatibility
        )
        
        logger.info("✓ DataLoader created successfully")
        
        # Fetch the first batch
        batch = next(iter(dataloader))
        
        # Extract images and labels from batch
        images, labels = batch
        
        # Get batch shape
        batch_shape = list(images.shape)
        
        # Convert labels to list for JSON serialization
        sample_labels = labels.tolist()
        
        logger.info(f"✓ Successfully loaded first batch")
        logger.info(f"  Batch shape: {batch_shape}")
        logger.info(f"  Sample labels: {sample_labels}")
        
        return {
            "status": "success",
            "dataset_size": len(dataset),
            "batch_shape": batch_shape,
            "sample_labels": sample_labels,
            "message": f"Successfully loaded batch with shape {batch_shape}"
        }
        
    except FileNotFoundError as e:
        error_msg = f"File not found: {str(e)}"
        logger.error(f"✗ {error_msg}")
        return {
            "status": "error",
            "error_type": "FileNotFoundError",
            "error_message": error_msg,
            "hint": "Check if Docker volumes are mounted correctly. Expected paths:",
            "expected_paths": {
                "csv": "/data/processed/clean_labels.csv",
                "images": "/data/processed/train"
            }
        }
    
    except Exception as e:
        error_msg = str(e)
        error_type = type(e).__name__
        logger.error(f"✗ Error loading data: {error_type}: {error_msg}")
        return {
            "status": "error",
            "error_type": error_type,
            "error_message": error_msg,
            "hint": "Check the error type and message for debugging"
        }


# ============ Model Information ============


async def get_models_info():
    """Get information about loaded models"""
    models = get_models()
    return models.get_model_info()


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
