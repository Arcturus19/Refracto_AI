"""
XAI (Explainable AI) Engine for Refracto AI
Generates visual explanations using Grad-CAM and other techniques
"""

import torch
import torch.nn as nn
from pytorch_grad_cam import GradCAM
from pytorch_grad_cam.utils.image import show_cam_on_image
from pytorch_grad_cam.utils.model_targets import ClassifierOutputTarget
import numpy as np
from PIL import Image
import cv2
import base64
import io
from typing import Optional, Tuple, List
import logging

logger = logging.getLogger(__name__)


class VisualExplainer:
    """
    Generate visual explanations for model predictions using Grad-CAM
    """
    
    def __init__(self):
        """Initialize the visual explainer"""
        self.cam_algorithm = None
    
    def generate_heatmap(
        self,
        model: nn.Module,
        input_tensor: torch.Tensor,
        original_image: Optional[np.ndarray] = None,
        target_layer: Optional[nn.Module] = None,
        target_class: Optional[int] = None,
        use_cuda: bool = False
    ) -> Tuple[np.ndarray, str]:
        """
        Generate Grad-CAM heatmap for model prediction
        
        Args:
            model: PyTorch model
            input_tensor: Input tensor (C, H, W) or (B, C, H, W)
            original_image: Original RGB image as numpy array (H, W, 3) normalized to [0, 1]
            target_layer: Target convolutional layer (if None, automatically detected)
            target_class: Target class for CAM (if None, uses predicted class)
            use_cuda: Whether to use CUDA
            
        Returns:
            Tuple of (heatmap_overlay as numpy array, base64 encoded image string)
        """
        try:
            # Ensure input tensor has batch dimension
            if input_tensor.dim() == 3:
                input_tensor = input_tensor.unsqueeze(0)
            
            # Move to device
            device = torch.device('cuda' if use_cuda and torch.cuda.is_available() else 'cpu')
            input_tensor = input_tensor.to(device)
            
            # Auto-detect target layer if not provided
            if target_layer is None:
                target_layer = self._get_target_layer(model)
                logger.info(f"Auto-detected target layer: {target_layer.__class__.__name__}")
            
            # Create Grad-CAM object
            cam = GradCAM(
                model=model,
                target_layers=[target_layer],
                use_cuda=use_cuda
            )
            
            # Set target class
            targets = None
            if target_class is not None:
                targets = [ClassifierOutputTarget(target_class)]
            
            # Generate CAM
            grayscale_cam = cam(
                input_tensor=input_tensor,
                targets=targets
            )
            
            # Get the CAM for the first image in batch
            grayscale_cam = grayscale_cam[0, :]
            
            # Prepare original image for overlay
            if original_image is None:
                # If no original image provided, denormalize the input tensor
                original_image = self._denormalize_tensor(input_tensor[0])
            
            # Ensure original_image is in correct format (H, W, 3) with values [0, 1]
            if original_image.max() > 1.0:
                original_image = original_image / 255.0
            
            # Generate visualization
            visualization = show_cam_on_image(
                original_image,
                grayscale_cam,
                use_rgb=True,
                image_weight=0.6  # Adjust transparency
            )
            
            # Convert to base64
            base64_image = self._numpy_to_base64(visualization)
            
            logger.info(f"✓ Generated Grad-CAM heatmap (shape: {visualization.shape})")
            
            return visualization, base64_image
            
        except Exception as e:
            logger.error(f"✗ Error generating heatmap: {str(e)}")
            raise
    
    def _get_target_layer(self, model: nn.Module) -> nn.Module:
        """
        Automatically detect the target layer for Grad-CAM
        
        For EfficientNet: Usually the last convolutional layer
        For other models: Find the last Conv2d layer
        
        Args:
            model: PyTorch model
            
        Returns:
            Target layer module
        """
        # Check if it's an EfficientNet model (timm)
        if hasattr(model, 'blocks'):
            # EfficientNet from timm
            return model.blocks[-1]
        
        elif hasattr(model, 'features'):
            # Models with 'features' attribute (e.g., VGG, ResNet)
            return model.features[-1]
        
        elif hasattr(model, 'layer4'):
            # ResNet-style models
            return model.layer4[-1]
        
        else:
            # Generic: find last Conv2d layer
            target_layer = None
            for name, module in model.named_modules():
                if isinstance(module, nn.Conv2d):
                    target_layer = module
            
            if target_layer is None:
                raise ValueError("Could not find a suitable target layer. Please specify target_layer manually.")
            
            return target_layer
    
    def _denormalize_tensor(self, tensor: torch.Tensor) -> np.ndarray:
        """
        Denormalize a tensor to original image space
        
        Args:
            tensor: Normalized tensor (C, H, W)
            
        Returns:
            Denormalized image as numpy array (H, W, 3) with values [0, 1]
        """
        # ImageNet normalization values
        mean = torch.tensor([0.485, 0.456, 0.406]).view(3, 1, 1)
        std = torch.tensor([0.229, 0.224, 0.225]).view(3, 1, 1)
        
        # Denormalize
        tensor = tensor.cpu() * std + mean
        tensor = torch.clamp(tensor, 0, 1)
        
        # Convert to numpy and transpose
        image = tensor.permute(1, 2, 0).numpy()
        
        return image
    
    def _numpy_to_base64(self, image: np.ndarray) -> str:
        """
        Convert numpy image to base64 string
        
        Args:
            image: Numpy array (H, W, 3) with values [0, 255]
            
        Returns:
            Base64 encoded string
        """
        # Convert to uint8 if needed
        if image.dtype != np.uint8:
            image = (image * 255).astype(np.uint8) if image.max() <= 1.0 else image.astype(np.uint8)
        
        # Convert to PIL Image
        pil_image = Image.fromarray(image)
        
        # Save to bytes buffer
        buffer = io.BytesIO()
        pil_image.save(buffer, format='PNG')
        buffer.seek(0)
        
        # Encode to base64
        base64_string = base64.b64encode(buffer.read()).decode('utf-8')
        
        return f"data:image/png;base64,{base64_string}"
    
    def generate_multiple_heatmaps(
        self,
        model: nn.Module,
        input_tensor: torch.Tensor,
        original_image: np.ndarray,
        target_classes: List[int],
        target_layer: Optional[nn.Module] = None
    ) -> List[Tuple[int, np.ndarray, str]]:
        """
        Generate heatmaps for multiple target classes
        
        Args:
            model: PyTorch model
            input_tensor: Input tensor
            original_image: Original RGB image
            target_classes: List of target class indices
            target_layer: Target convolutional layer
            
        Returns:
            List of tuples (class_id, heatmap_array, base64_string)
        """
        results = []
        
        for class_id in target_classes:
            try:
                heatmap, base64_img = self.generate_heatmap(
                    model=model,
                    input_tensor=input_tensor,
                    original_image=original_image,
                    target_layer=target_layer,
                    target_class=class_id
                )
                results.append((class_id, heatmap, base64_img))
            except Exception as e:
                logger.error(f"Failed to generate heatmap for class {class_id}: {str(e)}")
        
        return results
    
    def generate_attention_map(
        self,
        model: nn.Module,
        input_tensor: torch.Tensor,
        original_image: Optional[np.ndarray] = None
    ) -> Tuple[np.ndarray, str]:
        """
        Generate attention map (simplified version of heatmap)
        
        Args:
            model: PyTorch model
            input_tensor: Input tensor
            original_image: Original RGB image
            
        Returns:
            Tuple of (attention_map as numpy array, base64 encoded image)
        """
        return self.generate_heatmap(
            model=model,
            input_tensor=input_tensor,
            original_image=original_image
        )


# Singleton instance
_explainer_instance: Optional[VisualExplainer] = None


def get_explainer() -> VisualExplainer:
    """
    Get or create the singleton VisualExplainer instance
    
    Returns:
        VisualExplainer instance
    """
    global _explainer_instance
    
    if _explainer_instance is None:
        _explainer_instance = VisualExplainer()
    
    return _explainer_instance


# Utility function for easy access
def generate_grad_cam(
    model: nn.Module,
    input_tensor: torch.Tensor,
    original_image: Optional[np.ndarray] = None,
    target_class: Optional[int] = None
) -> str:
    """
    Convenience function to generate Grad-CAM and return base64 string
    
    Args:
        model: PyTorch model
        input_tensor: Input tensor
        original_image: Original RGB image
        target_class: Target class for CAM
        
    Returns:
        Base64 encoded heatmap image
    """
    explainer = get_explainer()
    _, base64_img = explainer.generate_heatmap(
        model=model,
        input_tensor=input_tensor,
        original_image=original_image,
        target_class=target_class
    )
    return base64_img
