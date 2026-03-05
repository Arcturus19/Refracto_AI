# ML Service Setup Guide

## Overview

The ML Service provides AI-powered medical image analysis using deep learning models.

## Configuration

### Port
- **API**: http://localhost:8004
- **Documentation**: http://localhost:8004/docs

### Models Supported

1. **Fundus Images** (Retinal photography)
   - Model: EfficientNet-B0 (via timm)
   - Analysis: Diabetic retinopathy detection
   
2. **OCT Images** (Optical Coherence Tomography)
   - Model: Vision Transformer (ViT)
   - Analysis: Retinal layer analysis

## Directory Structure

```
ml_service/
├── main.py              # FastAPI application
├── config.py            # Configuration settings
├── requirements.txt     # Python dependencies
├── Dockerfile           # Container build instructions
├── .dockerignore        # Files to exclude from build
└── models/              # Pre-trained models directory
    ├── fundus_model.pth
    └── oct_model.pth
```

## Environment Variables

```env
MODEL_PATH=/app/models
DEVICE=cpu  # or 'cuda' for GPU
```

## Installing Dependencies

The service uses:
- **PyTorch 2.1.2** - Deep learning framework
- **timm** - Pre-trained vision models (EfficientNet)
- **transformers** - Hugging Face transformers (ViT)
- **PIL/numpy** - Image processing

## Running the Service

### With Docker Compose

```powershell
cd "c:\Users\VICTUS\Desktop\Refracto AI\Refracto-AI-Backend"
docker-compose up -d ml_service --build
```

### Standalone (Development)

```powershell
cd services/ml_service
pip install -r requirements.txt
python main.py
```

## API Endpoints

### Health Check
```http
GET http://localhost:8004/health
```

**Response:**
```json
{
  "status": "healthy",
  "service": "ml_service",
  "device": "cpu",
  "models_loaded": true
}
```

### Analyze Fundus Image
```http
POST http://localhost:8004/analyze/fundus
Content-Type: multipart/form-data

file: [image file]
```

### Analyze OCT Image
```http
POST http://localhost:8004/analyze/oct
Content-Type: multipart/form-data

file: [image file]
```

### General Prediction
```http
POST http://localhost:8004/predict?image_type=fundus
Content-Type: multipart/form-data

file: [image file]
```

**Response:**
```json
{
  "predictions": {
    "diabetic_retinopathy": {
      "probability": 0.85,
      "class": "moderate",
      "confidence": 0.85
    },
    "glaucoma": {
      "probability": 0.23,
      "class": "low_risk",
      "confidence": 0.77
    }
  },
  "processing_time_ms": 245
}
```

### Model Information
```http
GET http://localhost:8004/models/info
```

## Model Loading (Future Implementation)

Models will be automatically loaded on service startup. The models directory is mapped to persist downloaded models:

```python
# Example model loading (to be implemented)
import torch
import timm

# Load EfficientNet for fundus images
fundus_model = timm.create_model('efficientnet_b0', pretrained=True)
fundus_model.eval()

# Load ViT for OCT images
from transformers import ViTForImageClassification
oct_model = ViTForImageClassification.from_pretrained('google/vit-base-patch16-224')
oct_model.eval()
```

## GPU Support

To enable GPU acceleration:

1. Update `docker-compose.yml`:
```yaml
ml_service:
  deploy:
    resources:
      reservations:
        devices:
          - driver: nvidia
            count: 1
            capabilities: [gpu]
  environment:
    DEVICE: cuda
```

2. Install NVIDIA Docker runtime on host

## Memory Requirements

- **CPU Mode**: ~4GB RAM
- **GPU Mode**: ~8GB RAM + GPU memory
- **Model Storage**: ~500MB - 2GB per model

## Performance

Expected inference times (CPU):
- Fundus analysis: ~200-500ms per image
- OCT analysis: ~300-600ms per image

With GPU: 10-20x faster

## Integration with Imaging Service

The ML service can be called from the imaging service after upload:

```python
import requests

# After uploading image to MinIO
response = requests.post(
    "http://ml_service:8000/predict",
    files={"file": image_data},
    params={"image_type": "fundus"}
)

predictions = response.json()
```

## Troubleshooting

### Service won't start
```powershell
docker logs refracto_ml_service
```

### Out of memory
Reduce batch size in `config.py`:
```python
BATCH_SIZE = 1  # Process one image at a time
```

### Slow inference
- Check if DEVICE=cpu (switch to GPU if available)
- Reduce MAX_IMAGE_SIZE in config
- Use smaller models (efficientnet_b0 instead of b7)

## Next Steps

1. **Implement Model Loading** - Load actual pre-trained models
2. **Add Preprocessing** - Image normalization and resizing
3. **Implement Inference** - Run predictions through models
4. **Post-processing** - Convert model outputs to predictions
5. **Add More Models** - Additional disease detection
6. **Batch Processing** - Process multiple images efficiently
7. **Model Versioning** - Track and update models

---

**ML Service is ready for AI model integration!** 🤖🧠
