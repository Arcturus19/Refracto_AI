"""
Image preprocessing utilities for ML inference
"""

import torch
from PIL import Image
import torchvision.transforms as transforms
from typing import Union
import io
import numpy as np


class ImagePreprocessor:
    """
    Preprocessing pipelines for different image types
    """
    
    def __init__(self):
        """Initialize preprocessing transforms"""
        
        # Standard ImageNet normalization
        self.normalize = transforms.Normalize(
            mean=[0.485, 0.456, 0.406],
            std=[0.229, 0.224, 0.225]
        )
        
        # Fundus preprocessing (224x224)
        self.fundus_transform = transforms.Compose([
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            self.normalize
        ])
        
        # OCT preprocessing (224x224 for ViT)
        self.oct_transform = transforms.Compose([
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            self.normalize
        ])
        
        # Refraction preprocessing (same as fundus)
        self.refraction_transform = self.fundus_transform
    
    def preprocess(
        self,
        image: Union[Image.Image, bytes, np.ndarray],
        task_type: str = 'fundus'
    ) -> torch.Tensor:
        """
        Preprocess image for ML inference
        
        Args:
            image: PIL Image, bytes, or numpy array
            task_type: Type of task ('fundus', 'oct', 'refraction')
            
        Returns:
            Preprocessed image tensor
        """
        # Convert to PIL Image if needed
        if isinstance(image, bytes):
            # Safe parsing of raw byte streams from FastAPI
            try:
                image = Image.open(io.BytesIO(image))
            except Exception as e:
                import logging
                logging.getLogger(__name__).error(f"Failed to load image bytes: {e}")
                raise
        elif isinstance(image, np.ndarray):
            image = Image.fromarray(image)
        
        # Convert to RGB if needed
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        # Apply appropriate transform
        if task_type == 'fundus':
            tensor = self.fundus_transform(image)
        elif task_type == 'oct':
            tensor = self.oct_transform(image)
        elif task_type == 'refraction':
            tensor = self.refraction_transform(image)
        else:
            raise ValueError(f"Unknown task_type: {task_type}")
        
        return tensor


# Global preprocessor instance
_preprocessor = None


def get_preprocessor() -> ImagePreprocessor:
    """Get singleton preprocessor instance"""
    global _preprocessor
    if _preprocessor is None:
        _preprocessor = ImagePreprocessor()
    return _preprocessor
