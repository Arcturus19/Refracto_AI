import asyncio
import torch
import io
import traceback
from PIL import Image
import os
import sys

sys.stdout = open('debug.log', 'w')
sys.stderr = sys.stdout

# Add the ml_service to path so we can import its modules
sys.path.append(os.path.join(os.path.dirname(__file__), "services", "ml_service"))
from core.model_loader import get_models

def create_dummy_image() -> torch.Tensor:
    # 3x224x224 dummy image tensor for testing
    return torch.randn(1, 3, 224, 224)

def test_hybrid_inference():
    print("Testing Hybrid MTL Pipeline...")
    try:
        models = get_models()
        models.load_models()
        print("Models loaded successfully.")
    except Exception as e:
        print(f"Failed to load models: {e}")
        return

    # Create dummy data
    fundus_img = create_dummy_image()
    oct_img = create_dummy_image()
    
    # Clinical Data
    clinical_feats = torch.tensor([[0.5, 0.375, 0.0, 0.66, 0.0]], dtype=torch.float32)

    try:
        print("Running prediction...")
        result = models.predict_mtl(fundus_img, oct_img, clinical_feats)
        print("Prediction Successful!")
        print(f"DR Label: {result['dr_label'].item()}")
        print(f"Glaucoma Prob: {result['glaucoma_prob'].item():.4f}")
        print(f"Refraction (Sphere, Cyl, Axis): {result['refraction'][0].tolist()}")
        print(f"Correction Factor Applied: {result['correction_factor']}")
    except Exception as e:
        traceback.print_exc()
        print(f"Prediction failed: {e}")

if __name__ == "__main__":
    test_hybrid_inference()
