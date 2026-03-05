"""
ML Service - FastAPI Application
Machine Learning microservice for medical image analysis
"""

from fastapi import FastAPI, UploadFile, File, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from config import settings
from core.model_loader import get_models, load_models_on_startup
from core.preprocessing import get_preprocessor
from core.xai_engine import get_explainer
from PIL import Image
import io
import numpy as np
import logging
import time
import torch
from torchvision import transforms
from torch.utils.data import DataLoader
from core.dataset_loader import RefractoDataset


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


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
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# CORS middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Update with specific origins in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


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
            "test_data_loading": "/test-data-loading"
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring"""
    return {
        "status": "healthy",
        "service": "ml_service",
        "device": settings.DEVICE,
        "models_loaded": False  # Will be updated when models are loaded
    }


# ============ ML Prediction Endpoints ============

@app.post("/analyze/fundus")
async def analyze_fundus(file: UploadFile = File(...)):
    """
    Analyze fundus image for diabetic retinopathy
    
    Returns DR severity classification with probabilities
    """
    start_time = time.time()
    
    try:
        # Reset file pointer and read bytes safely
        await file.seek(0)
        image_bytes = await file.read()
        
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
        
        return result
        
    except Exception as e:
        logger.error(f"✗ Fundus analysis error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Analysis failed: {str(e)}"
        )


@app.post("/analyze/oct")
async def analyze_oct(file: UploadFile = File(...)):
    """
    Analyze OCT image for retinal conditions
    
    Returns OCT-based condition classification
    """
    start_time = time.time()
    
    try:
        # Reset file pointer and read bytes safely
        await file.seek(0)
        image_bytes = await file.read()
        
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
        
        return result
        
    except Exception as e:
        logger.error(f"✗ OCT analysis error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Analysis failed: {str(e)}"
        )


@app.post("/analyze/refraction")
async def analyze_refraction(file: UploadFile = File(...)):
    """
    Analyze fundus image for refraction measurements
    
    Returns predicted Sphere, Cylinder, and Axis values
    """
    start_time = time.time()
    
    try:
        # Reset file pointer and read bytes safely
        await file.seek(0)
        image_bytes = await file.read()
        
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
        
        return result
        
    except Exception as e:
        logger.error(f"✗ Refraction analysis error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Analysis failed: {str(e)}"
        )


@app.post("/predict")
async def predict(
    file: UploadFile = File(...),
    image_type: str = "fundus"
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
        # Reset file pointer and read bytes safely
        await file.seek(0)
        image_bytes = await file.read()
        
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
        
        return result
        
    except Exception as e:
        logger.error(f"✗ Prediction error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Prediction failed: {str(e)}"
        )


# ============ Simplified Prediction Endpoints ============

@app.post("/predict/refraction")
async def predict_refraction(file: UploadFile = File(...)):
    """
    Simplified refraction prediction endpoint
    
    Returns:
        JSON with sphere, cylinder, and axis values
        Example: { "sphere": -2.50, "cylinder": -0.75, "axis": 180 }
    """
    try:
        # Reset file pointer and read bytes safely
        await file.seek(0)
        image_bytes = await file.read()
        
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
        
        return {
            "sphere": measurements['sphere'],
            "cylinder": measurements['cylinder'],
            "axis": measurements['axis']
        }
        
    except Exception as e:
        logger.error(f"✗ Refraction prediction error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Prediction failed: {str(e)}"
        )


@app.post("/predict/pathology")
async def predict_pathology(file: UploadFile = File(...)):
    """
    Simplified pathology prediction endpoint
    
    Runs fundus image through EfficientNet for DR grading and glaucoma risk
    
    Returns:
        JSON with DR grade and glaucoma risk
        Example: { "dr_grade": 2, "glaucoma_risk": 0.85 }
    """
    try:
        # Reset file pointer and read bytes safely
        await file.seek(0)
        image_bytes = await file.read()
        
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
        
        return {
            "dr_grade": dr_grade,
            "glaucoma_risk": glaucoma_risk
        }
        
    except Exception as e:
        logger.error(f"✗ Pathology prediction error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Prediction failed: {str(e)}"
        )


# ============ Explainability Endpoints (XAI) ============

@app.post("/explain/pathology")
async def explain_pathology(file: UploadFile = File(...)):
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
        # Reset file pointer and read bytes safely
        await file.seek(0)
        image_bytes = await file.read()
        
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
        
        return {
            "diagnosis": diagnosis,
            "heatmap_base64": heatmap_base64,
            "processing_time_ms": processing_time,
            "explanation": f"The highlighted regions show areas that most influenced the {result['prediction']['class']} diagnosis."
        }
        
    except Exception as e:
        logger.error(f"✗ Explanation generation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Explanation generation failed: {str(e)}"
        )


# ============ Testing Endpoints ============

@app.get("/test-data-loading")
async def test_data_loading():
    """
    Test endpoint for RefractoDataset and DataLoader
    
    Verifies that the dataset can be loaded and batched correctly
    
    Returns:
        JSON summary with batch shape and sample labels
    """
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
