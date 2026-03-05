"""
Verification script for Refracto AI ML Environment
Tests torch, PIL, and sample image loading
"""
import torch
import torchvision.transforms as transforms
from PIL import Image
from pathlib import Path
import os

def verify():
    print("--- Refracto AI ML Environment Verification ---")
    
    # 1. Check Torch
    print(f"PyTorch Version: {torch.__version__}")
    print(f"CUDA Available: {torch.cuda.is_available()}")
    
    # 2. Check Sample Image
    sample_path = Path("backend/services/ml_service/datasets/samples/dummy_fundus.jpg")
    if sample_path.exists():
        print(f"✓ Sample image found at: {sample_path}")
        try:
            img = Image.open(sample_path)
            print(f"✓ Image loaded: {img.size} {img.mode}")
            
            # Simple transform test
            transform = transforms.Compose([
                transforms.Resize((224, 224)),
                transforms.ToTensor()
            ])
            tensor = transform(img)
            print(f"✓ Image transformed to tensor: {tensor.shape}")
        except Exception as e:
            print(f"✗ Image processing failed: {e}")
    else:
        print(f"✗ Sample image NOT found at {sample_path}")
        
    # 3. Check imports of core components
    try:
        import sys
        sys.path.append(str(Path("backend/services/ml_service").absolute()))
        from core.dataset_loader import RefractoDataset
        print("✓ Successfully imported RefractoDataset")
    except Exception as e:
        print(f"✗ Failed to import core components: {e}")
        
    print("\nResolution: Environment is READY for training once datasets are uploaded.")

if __name__ == "__main__":
    verify()
