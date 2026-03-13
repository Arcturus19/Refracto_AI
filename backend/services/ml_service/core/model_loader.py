"""
Model Loader for Refracto AI
Singleton pattern for loading and managing ML models
"""

import torch
import torch.nn as nn
import timm
from transformers import ViTForImageClassification, ViTImageProcessor
from typing import Dict, Optional, Tuple
import logging
import os
from config import settings
from core.fusion import MultiHeadFusion, MultiTaskFusionHead
from core.clinical_fusion import ClinicalDataEncoder
from core.refracto_pathological_link import RefractoPathologicalLink

logger = logging.getLogger(__name__)


class RefractionHead(nn.Module):
    """
    Regression head for predicting refraction measurements
    Outputs: Sphere, Cylinder, Axis
    """
    
    def __init__(self, input_features: int = 1000):
        super(RefractionHead, self).__init__()
        
        # Multi-layer regression head
        self.regressor = nn.Sequential(
            nn.Linear(input_features, 512),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(512, 256),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(256, 128),
            nn.ReLU(),
            nn.Linear(128, 3)  # Sphere, Cylinder, Axis
        )
        
        # Output layer normalizations
        # Typical ranges: Sphere (-20 to +20), Cylinder (0 to -6), Axis (0 to 180)
        
    def forward(self, x):
        """
        Forward pass
        
        Args:
            x: Feature tensor from backbone model
            
        Returns:
            Tensor of shape (batch_size, 3) containing [sphere, cylinder, axis]
        """
        output = self.regressor(x)
        
        # Apply constraints to outputs
        sphere = torch.tanh(output[:, 0]) * 20  # Range: -20 to +20
        cylinder = -torch.sigmoid(output[:, 1]) * 6  # Range: 0 to -6
        axis = torch.sigmoid(output[:, 2]) * 180  # Range: 0 to 180
        
        return torch.stack([sphere, cylinder, axis], dim=1)


class RefractoModels:
    """
    Singleton class for managing all ML models
    """
    
    _instance = None
    _models_loaded = False
    
    def __new__(cls):
        """Singleton pattern - ensure only one instance exists"""
        if cls._instance is None:
            cls._instance = super(RefractoModels, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Initialize model containers"""
        if not self._models_loaded:
            self.device = torch.device(settings.DEVICE)
            logger.info(f"🖥️  Using device: {self.device}")
            
            # Model containers
            self.fundus_model: Optional[nn.Module] = None
            self.oct_model: Optional[nn.Module] = None
            self.refraction_backbone: Optional[nn.Module] = None
            self.refraction_head: Optional[RefractionHead] = None
            
            # Hybrid Fusion + MTL Models
            self.fusion: Optional[MultiHeadFusion] = None
            self.mtl_head: Optional[MultiTaskFusionHead] = None
            self.clinical_encoder: Optional[ClinicalDataEncoder] = None
            self.refracto_link: Optional[RefractoPathologicalLink] = None
            
            # Image processors
            self.vit_processor: Optional[ViTImageProcessor] = None
            
            # Disease class mappings
            self.dr_classes = {
                0: "No DR",
                1: "Mild DR",
                2: "Moderate DR",
                3: "Severe DR",
                4: "Proliferative DR"
            }
    
    def load_models(self) -> bool:
        """
        Load all models into memory
        
        Returns:
            True if all models loaded successfully
        """
        try:
            logger.info("=" * 60)
            logger.info("🔧 Loading ML Models...")
            logger.info("=" * 60)
            
            # 1. Load Fundus Model (EfficientNet-B3 for DR grading)
            self._load_fundus_model()
            
            # 2. Load OCT Model (Vision Transformer)
            self._load_oct_model()
            
            # 3. Load Refraction Model (Regression)
            self._load_refraction_model()
            
            # 4. Load Hybrid Fusion Modules
            self._load_hybrid_fusion_models()
            
            RefractoModels._models_loaded = True
            logger.info("=" * 60)
            logger.info("✅ All models loaded successfully!")
            logger.info("=" * 60)
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error loading models: {str(e)}")
            return False
    
    def _load_fundus_model(self):
        """Load EfficientNet-B3 for fundus image analysis (DR grading)"""
        logger.info("📸 Loading Fundus Model (EfficientNet-B3)...")
        
        try:
            # Load pre-trained EfficientNet-B3
            self.fundus_model = timm.create_model(
                'efficientnet_b3',
                pretrained=True,
                num_classes=5  # 5 DR severity classes
            )
            
            # Move to device and set to evaluation mode
            self.fundus_model = self.fundus_model.to(self.device)
            self.fundus_model.eval()
            
            logger.info(f"   ✓ EfficientNet-B3 loaded with 5 output classes")
            logger.info(f"   ✓ Classes: {list(self.dr_classes.values())}")
            
        except Exception as e:
            logger.error(f"   ✗ Failed to load fundus model: {str(e)}")
            raise
    
    def _load_oct_model(self):
        """Load Vision Transformer for OCT image analysis"""
        logger.info("🔬 Loading OCT Model (Vision Transformer)...")
        
        try:
            # Load pre-trained ViT model
            model_name = "google/vit-base-patch16-224"
            
            # Load the model
            self.oct_model = ViTForImageClassification.from_pretrained(
                model_name,
                num_labels=3,  # Can be fine-tuned for specific OCT classifications
                ignore_mismatched_sizes=True
            )
            
            # Load the image processor
            self.vit_processor = ViTImageProcessor.from_pretrained(model_name)
            
            # Move to device and set to evaluation mode
            self.oct_model = self.oct_model.to(self.device)
            self.oct_model.eval()
            
            logger.info(f"   ✓ Vision Transformer loaded from {model_name}")
            logger.info(f"   ✓ Image processor loaded")
            
        except Exception as e:
            logger.error(f"   ✗ Failed to load OCT model: {str(e)}")
            raise
    
    def _load_refraction_model(self):
        """Load refraction measurement model (regression)"""
        logger.info("👁️  Loading Refraction Model (Regression)...")
        
        try:
            # Use EfficientNet-B0 as backbone for speed
            self.refraction_backbone = timm.create_model(
                'efficientnet_b0',
                pretrained=True,
                num_classes=0,  # Remove classification head
                global_pool=''  # Remove global pooling to get features
            )
            
            # Get the number of output features from the backbone
            with torch.no_grad():
                dummy_input = torch.randn(1, 3, 224, 224)
                backbone_features = self.refraction_backbone(dummy_input)
                
                # Global average pooling
                pooled_features = torch.nn.functional.adaptive_avg_pool2d(
                    backbone_features, (1, 1)
                ).flatten(1)
                
                num_features = pooled_features.shape[1]
            
            # Create regression head
            self.refraction_head = RefractionHead(input_features=num_features)
            
            # Move to device and set to evaluation mode
            self.refraction_backbone = self.refraction_backbone.to(self.device)
            self.refraction_head = self.refraction_head.to(self.device)
            
            self.refraction_backbone.eval()
            self.refraction_head.eval()
            
            logger.info(f"   ✓ EfficientNet-B0 backbone loaded")
            logger.info(f"   ✓ Regression head created ({num_features} -> 3)")
            logger.info(f"   ✓ Outputs: Sphere, Cylinder, Axis")
            
        except Exception as e:
            logger.error(f"   ✗ Failed to load refraction model: {str(e)}")
            raise
            
    def _load_hybrid_fusion_models(self):
        """Load Hybrid Fusion, clinical encoder, and refracto-pathological link"""
        logger.info("🔗 Loading Hybrid Fusion Modules...")
        try:
            self.fusion = MultiHeadFusion(fundus_dim=1536, oct_dim=768, fused_dim=512, num_heads=8).to(self.device).eval()
            self.clinical_encoder = ClinicalDataEncoder(input_dim=5, encoded_dim=64).to(self.device).eval()
            self.mtl_head = MultiTaskFusionHead(input_dim=512, clinical_dim=64, num_dr_classes=5, num_glaucoma_classes=2).to(self.device).eval()
            self.refracto_link = RefractoPathologicalLink().to(self.device).eval()
            
            logger.info("   ✓ MultiHeadFusion loaded")
            logger.info("   ✓ ClinicalDataEncoder loaded")
            logger.info("   ✓ MultiTaskFusionHead loaded")
            logger.info("   ✓ RefractoPathologicalLink loaded")
        except Exception as e:
            logger.error(f"   ✗ Failed to load hybrid fusion models: {str(e)}")
            raise
    
    @torch.no_grad()
    def predict(
        self,
        image_tensor: torch.Tensor,
        task_type: str
    ) -> Dict:
        """
        Run prediction on preprocessed image tensor
        
        Args:
            image_tensor: Preprocessed image tensor (C, H, W) or (B, C, H, W)
            task_type: Type of task - 'fundus', 'oct', or 'refraction'
            
        Returns:
            Dictionary containing predictions
        """
        if not self._models_loaded:
            raise RuntimeError("Models not loaded. Call load_models() first.")
        
        # Ensure batch dimension
        if image_tensor.dim() == 3:
            image_tensor = image_tensor.unsqueeze(0)
        
        # Move to device
        image_tensor = image_tensor.to(self.device)
        
        # Route to appropriate model
        if task_type == 'fundus':
            return self._predict_fundus(image_tensor)
        elif task_type == 'oct':
            return self._predict_oct(image_tensor)
        elif task_type == 'refraction':
            return self._predict_refraction(image_tensor)
        else:
            raise ValueError(f"Unknown task_type: {task_type}")
            
    @torch.no_grad()
    def predict_mtl(self, fundus_image: torch.Tensor, oct_image: torch.Tensor, clinical_features: Optional[torch.Tensor] = None) -> Dict:
        """Multi-modal prediction using fused features + structured data."""
        if not self._models_loaded:
            raise RuntimeError("Models not loaded. Call load_models() first.")
            
        fundus_image = fundus_image.to(self.device)
        oct_image = oct_image.to(self.device)
        
        # Extract features (without classification head)
        try:
            # For EfficientNet, forward_features gets the pooled features
            fundus_features = self.fundus_model.forward_features(fundus_image) # Often (B, C, H, W)
            fundus_features = self.fundus_model.global_pool(fundus_features) # (B, 1000)
        except Exception:
            # Fallback
            fundus_features = self.refraction_backbone(fundus_image)
            fundus_features = torch.nn.functional.adaptive_avg_pool2d(fundus_features, (1, 1)).flatten(1)
            
        try:
            # For ViT
            vit_out = self.oct_model.vit(oct_image)
            if getattr(vit_out, 'pooler_output', None) is not None:
                oct_features = vit_out.pooler_output # (B, 768)
            else:
                oct_features = self.oct_model(oct_image, output_hidden_states=True).hidden_states[-1][:, 0, :]
        except Exception:
            # Fallback for ViT
            oct_features = self.oct_model(oct_image, output_hidden_states=True).hidden_states[-1][:, 0, :]
            
        # Fuse Visual modalities
        fused_visual = self.fusion(fundus_features, oct_features)
        
        # Encode clinical features if present
        encoded_clinical = None
        if clinical_features is not None:
            clinical_features = clinical_features.to(self.device)
            encoded_clinical = self.clinical_encoder(clinical_features)
            
        # Multi-task prediction
        dr_logits, glaucoma_logits, refraction = self.mtl_head(fused_visual, encoded_clinical)
        
        # Apply Refracto-pathological linking (Glaucoma correction)
        glaucoma_corrected = self.refracto_link(glaucoma_logits, refraction[:, 0])
        correction_factor = self.refracto_link.get_correction_factor(refraction[:, 0])
        
        return {
            "dr_logits": dr_logits,
            "dr_label": torch.argmax(dr_logits, dim=1),
            "glaucoma_logits": glaucoma_corrected,
            "glaucoma_prob": torch.softmax(glaucoma_corrected, dim=1)[:, 1],
            "refraction": refraction, # [sphere, cylinder, axis]
            "correction_factor": correction_factor
        }
    
    def _predict_fundus(self, image_tensor: torch.Tensor) -> Dict:
        """
        Predict diabetic retinopathy severity
        
        Args:
            image_tensor: Preprocessed fundus image
            
        Returns:
            Dictionary with DR predictions
        """
        # Forward pass
        logits = self.fundus_model(image_tensor)
        probabilities = torch.softmax(logits, dim=1)
        
        # Get prediction
        pred_class = torch.argmax(probabilities, dim=1).item()
        confidence = probabilities[0, pred_class].item()
        
        # Get all class probabilities
        class_probs = {
            self.dr_classes[i]: float(probabilities[0, i])
            for i in range(5)
        }
        
        return {
            "task": "fundus",
            "prediction": {
                "class": self.dr_classes[pred_class],
                "class_id": int(pred_class),
                "confidence": float(confidence)
            },
            "probabilities": class_probs,
            "severity_score": float(pred_class / 4.0)  # Normalized 0-1
        }
    
    def _predict_oct(self, image_tensor: torch.Tensor) -> Dict:
        """
        Predict OCT-based conditions
        
        Args:
            image_tensor: Preprocessed OCT image
            
        Returns:
            Dictionary with OCT predictions
        """
        # Forward pass
        outputs = self.oct_model(image_tensor)
        logits = outputs.logits
        probabilities = torch.softmax(logits, dim=1)
        
        # Get prediction
        pred_class = torch.argmax(probabilities, dim=1).item()
        confidence = probabilities[0, pred_class].item()
        
        # OCT class mapping (can be customized)
        oct_classes = {
            0: "Normal",
            1: "DME",  # Diabetic Macular Edema
            2: "AMD"   # Age-related Macular Degeneration
        }
        
        return {
            "task": "oct",
            "prediction": {
                "class": oct_classes.get(pred_class, f"Class {pred_class}"),
                "class_id": int(pred_class),
                "confidence": float(confidence)
            },
            "probabilities": {
                oct_classes.get(i, f"Class {i}"): float(probabilities[0, i])
                for i in range(probabilities.shape[1])
            }
        }
    
    def _predict_refraction(self, image_tensor: torch.Tensor) -> Dict:
        """
        Predict refraction measurements (Sphere, Cylinder, Axis)
        
        Args:
            image_tensor: Preprocessed fundus image
            
        Returns:
            Dictionary with refraction measurements
        """
        # Extract features from backbone
        features = self.refraction_backbone(image_tensor)
        
        # Global average pooling
        pooled_features = torch.nn.functional.adaptive_avg_pool2d(
            features, (1, 1)
        ).flatten(1)
        
        # Predict refraction values
        predictions = self.refraction_head(pooled_features)
        
        sphere = predictions[0, 0].item()
        cylinder = predictions[0, 1].item()
        axis = predictions[0, 2].item()
        
        return {
            "task": "refraction",
            "measurements": {
                "sphere": round(sphere, 2),
                "cylinder": round(cylinder, 2),
                "axis": round(axis, 1)
            },
            "prescription": f"SPH {sphere:+.2f} CYL {cylinder:.2f} × {axis:.0f}°"
        }
    
    def get_model_info(self) -> Dict:
        """Get information about loaded models"""
        return {
            "models_loaded": self._models_loaded,
            "device": str(self.device),
            "models": {
                "fundus": {
                    "name": "EfficientNet-B3",
                    "task": "Diabetic Retinopathy Grading",
                    "classes": list(self.dr_classes.values()),
                    "loaded": self.fundus_model is not None
                },
                "oct": {
                    "name": "Vision Transformer (ViT)",
                    "task": "OCT Analysis",
                    "loaded": self.oct_model is not None
                },
                "refraction": {
                    "name": "EfficientNet-B0 + Regression Head",
                    "task": "Refraction Measurement",
                    "outputs": ["Sphere", "Cylinder", "Axis"],
                    "loaded": self.refraction_backbone is not None and self.refraction_head is not None
                },
                "hybrid": {
                    "task": "Hybrid MTL + Clinical Data Fusion + XAI",
                    "loaded": self.fusion is not None and self.clinical_encoder is not None
                }
            }
        }


# Global instance - Singleton
_model_instance: Optional[RefractoModels] = None


def get_models() -> RefractoModels:
    """
    Get the singleton instance of RefractoModels
    
    Returns:
        RefractoModels instance
    """
    global _model_instance
    
    if _model_instance is None:
        _model_instance = RefractoModels()
        # Models will be loaded on first API call or at startup
    
    return _model_instance


def load_models_on_startup():
    """
    Load models on application startup
    Should be called in the FastAPI lifespan event
    """
    models = get_models()
    return models.load_models()
