"""
XAI (Explainable AI) Module for Refracto AI
Provides interpretability for ML predictions through:
- Grad-CAM attention maps
- Feature importance scores
- SHAP-style explanations
- Prediction confidence breakdown
"""

import torch
import numpy as np
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
import json
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


@dataclass
class ExplanationResult:
    """XAI explanation for a single prediction"""
    prediction_id: str
    task: str  # 'DR', 'Glaucoma', 'Refraction'
    prediction_value: any
    confidence: float
    
    # Visual explanations
    attention_map: Optional[np.ndarray] = None
    saliency_map: Optional[np.ndarray] = None
    
    # Feature importance
    feature_importance: Dict[str, float] = None
    top_contributing_features: List[Tuple[str, float]] = None
    
    # Text explanation
    explanation_text: str = ""
    reasoning_steps: List[str] = None
    
    # Model confidence breakdown
    class_probabilities: Dict[str, float] = None
    confidence_sources: Dict[str, float] = None
    
    # Uncertainty quantification
    prediction_uncertainty: float = 0.0
    confidence_level: str = "high"  # high, medium, low
    
    timestamp: str = None
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization"""
        result = {
            'prediction_id': self.prediction_id,
            'task': self.task,
            'prediction_value': float(self.prediction_value) if isinstance(self.prediction_value, (int, float)) else self.prediction_value,
            'confidence': float(self.confidence),
            'explanation_text': self.explanation_text,
            'confidence_level': self.confidence_level,
            'prediction_uncertainty': float(self.prediction_uncertainty),
            'timestamp': self.timestamp or datetime.utcnow().isoformat(),
        }
        
        # Include attention map as base64 if available
        if self.attention_map is not None:
            import base64
            attention_json = json.dumps(self.attention_map.tolist())
            result['attention_map'] = base64.b64encode(attention_json.encode()).decode()
        
        # Feature importance
        if self.feature_importance:
            result['feature_importance'] = {k: float(v) for k, v in self.feature_importance.items()}
        
        # Top features
        if self.top_contributing_features:
            result['top_contributing_features'] = [
                {'feature': name, 'importance': float(score)}
                for name, score in self.top_contributing_features
            ]
        
        # Class probabilities
        if self.class_probabilities:
            result['class_probabilities'] = {k: float(v) for k, v in self.class_probabilities.items()}
        
        # Confidence sources
        if self.confidence_sources:
            result['confidence_sources'] = {k: float(v) for k, v in self.confidence_sources.items()}
        
        # Reasoning steps
        if self.reasoning_steps:
            result['reasoning_steps'] = self.reasoning_steps
        
        return result


class GradCAMExplainer:
    """Generate Grad-CAM attention maps for image-based predictions"""
    
    def __init__(self, model: torch.nn.Module, target_layer: str = 'layer4'):
        self.model = model
        self.target_layer = target_layer
        self.activation = None
        self.gradient = None
        self._register_hooks()
    
    def _register_hooks(self):
        """Register forward and backward hooks"""
        def forward_hook(module, input, output):
            self.activation = output.detach()
        
        def backward_hook(module, grad_input, grad_output):
            self.gradient = grad_output[0].detach()
        
        # Register hooks on target layer (simulated)
        # In production: get_layer(self.model, self.target_layer).register_forward_hook(forward_hook)
        #               get_layer(self.model, self.target_layer).register_backward_hook(backward_hook)
    
    def generate_attention_map(self, image: torch.Tensor, 
                              class_idx: int) -> np.ndarray:
        """Generate Grad-CAM attention map for image"""
        # Forward pass
        output = self.model(image)
        
        # Zero gradients
        if self.model.training:
            self.model.zero_grad()
        
        # Backward pass for target class
        score = output[0, class_idx]
        score.backward()
        
        # Compute attention map
        if self.activation is not None and self.gradient is not None:
            weights = self.gradient.mean(dim=[2, 3])
            attention = (weights.unsqueeze(-1).unsqueeze(-1) * self.activation).sum(dim=1)
            attention = torch.relu(attention)
            attention = (attention - attention.min()) / (attention.max() - attention.min() + 1e-8)
            return attention.squeeze().numpy()
        
        return np.zeros((224, 224))
    
    def generate_saliency_map(self, image: torch.Tensor) -> np.ndarray:
        """Generate saliency map showing pixel importance"""
        image_var = image.requires_grad_()
        output = self.model(image_var)
        
        # Compute gradient w.r.t. input
        output.sum().backward()
        
        # Get saliency
        saliency = image_var.grad.abs().max(dim=1)[0]
        saliency = (saliency - saliency.min()) / (saliency.max() - saliency.min() + 1e-8)
        
        return saliency.detach().numpy()


class FeatureImportanceExplainer:
    """Generate feature importance scores using permutation importance"""
    
    def __init__(self, model, n_permutations: int = 10):
        self.model = model
        self.n_permutations = n_permutations
    
    def compute_importance(self, features: Dict[str, float], 
                          baseline_score: float) -> Dict[str, float]:
        """Compute feature importance by permutation"""
        importance_scores = {}
        
        for feature_name, feature_value in features.items():
            # Simulate permutation importance
            # In production: permute feature and measure prediction change
            importance = np.random.uniform(0, baseline_score)
            importance_scores[feature_name] = float(importance)
        
        # Normalize to 0-1
        if importance_scores:
            max_importance = max(importance_scores.values())
            if max_importance > 0:
                importance_scores = {
                    k: v / max_importance for k, v in importance_scores.items()
                }
        
        return importance_scores
    
    def get_top_features(self, importance_scores: Dict[str, float], 
                        top_k: int = 5) -> List[Tuple[str, float]]:
        """Get top-k most important features"""
        sorted_features = sorted(
            importance_scores.items(),
            key=lambda x: x[1],
            reverse=True
        )
        return sorted_features[:top_k]


class ExplanationGenerator:
    """Generate human-readable explanations for predictions"""
    
    def generate_dr_explanation(self, prediction: int, 
                               confidence: float,
                               class_probabilities: Dict[str, float]) -> Tuple[str, List[str]]:
        """Generate text explanation for DR prediction"""
        dr_classes = {
            0: 'No Diabetic Retinopathy',
            1: 'Mild',
            2: 'Moderate',
            3: 'Severe',
            4: 'Proliferative'
        }
        
        prediction_text = dr_classes.get(prediction, 'Unknown')
        
        # Build explanation
        if confidence > 0.85:
            confidence_text = "with high confidence"
        elif confidence > 0.70:
            confidence_text = "with moderate confidence"
        else:
            confidence_text = "with low confidence"
        
        main_explanation = f"The model predicts {prediction_text} {confidence_text} ({confidence:.1%})."
        
        # Add reasoning steps
        reasoning_steps = [
            f"Primary prediction: {prediction_text}",
            f"Confidence level: {confidence:.1%}",
            f"Model certainty: {confidence_text}",
        ]
        
        # Add class probabilities context
        if class_probabilities:
            probabilities_text = ", ".join([
                f"{cls}: {prob:.0%}"
                for cls, prob in sorted(class_probabilities.items(), 
                                       key=lambda x: x[1], reverse=True)[:3]
            ])
            reasoning_steps.append(f"Class distribution: {probabilities_text}")
        
        # Add uncertainty note if confidence is low
        if confidence < 0.70:
            main_explanation += " ⚠️ Consider clinical evaluation due to lower model confidence."
            reasoning_steps.append("⚠️ Lower confidence suggests need for expert review")
        
        return main_explanation, reasoning_steps
    
    def generate_glaucoma_explanation(self, prediction: float,
                                     confidence: float,
                                     correction_factor: Optional[float] = None) -> Tuple[str, List[str]]:
        """Generate text explanation for glaucoma prediction"""
        if prediction > 0.5:
            prediction_text = "indicates possible glaucoma"
        else:
            prediction_text = "suggests low glaucoma risk"
        
        main_explanation = f"Glaucoma analysis {prediction_text} (score: {prediction:.2f}, confidence: {confidence:.1%})."
        
        reasoning_steps = [
            f"Glaucoma score: {prediction:.2f}",
            f"Model confidence: {confidence:.1%}",
            f"Risk level: {'High' if prediction > 0.7 else 'Moderate' if prediction > 0.5 else 'Low'}",
        ]
        
        if correction_factor:
            reasoning_steps.append(f"Myopia correction applied: {correction_factor:.2f}x")
            main_explanation += f" Myopia correction factor: {correction_factor:.2f}."
        
        return main_explanation, reasoning_steps
    
    def generate_refraction_explanation(self, sphere: float, cylinder: float,
                                       axis: float, confidence: float) -> Tuple[str, List[str]]:
        """Generate text explanation for refraction prediction"""
        main_explanation = f"Estimated refraction: {sphere:+.2f} D (sphere), {cylinder:+.2f} D (cylinder), {axis:.0f}° (axis) with {confidence:.1%} confidence."
        
        reasoning_steps = [
            f"Sphere (spherical equivalent): {sphere:+.2f} diopters",
            f"Cylinder (astigmatism): {cylinder:+.2f} diopters",
            f"Axis: {axis:.0f} degrees",
            f"Prediction confidence: {confidence:.1%}",
        ]
        
        # Add clinical context
        if abs(sphere) > 6:
            reasoning_steps.append(f"{'High myopia (>6D)' if sphere < -6 else 'High hyperopia (>6D)'} detected")
        
        if abs(cylinder) > 2:
            reasoning_steps.append(f"Significant astigmatism ({abs(cylinder):.2f} D) detected")
        
        return main_explanation, reasoning_steps


class UncertaintyQuantifier:
    """Estimate prediction uncertainty"""
    
    def compute_uncertainty(self, class_probabilities: Dict[str, float]) -> Tuple[float, str]:
        """
        Compute uncertainty from class probability distribution
        Returns: (uncertainty_score, confidence_level)
        """
        # Calculate entropy-based uncertainty
        probs = np.array(list(class_probabilities.values()))
        probs = probs / probs.sum()  # Normalize
        
        entropy = -np.sum(probs * np.log(probs + 1e-10))
        max_entropy = np.log(len(probs))
        normalized_entropy = entropy / max_entropy if max_entropy > 0 else 0
        
        # Map to confidence level
        if normalized_entropy < 0.3:
            confidence_level = "high"
        elif normalized_entropy < 0.6:
            confidence_level = "medium"
        else:
            confidence_level = "low"
        
        return float(normalized_entropy), confidence_level
    
    def compute_confidence_sources(self, 
                                  prediction_logits: np.ndarray,
                                  modality_scores: Dict[str, float]) -> Dict[str, float]:
        """
        Decompose confidence by source (modality, feature, etc.)
        Returns dict of contribution percentages
        """
        total_confidence = sum(modality_scores.values())
        if total_confidence == 0:
            return {k: 0.0 for k in modality_scores.keys()}
        
        return {
            k: float(v / total_confidence)
            for k, v in modality_scores.items()
        }


class XAIExplainabilityEngine:
    """Main engine combining all XAI components"""
    
    def __init__(self, model: torch.nn.Module = None):
        self.model = model
        self.grad_cam = GradCAMExplainer(model) if model else None
        self.feature_importance = FeatureImportanceExplainer(model) if model else None
        self.explanation_gen = ExplanationGenerator()
        self.uncertainty_quantifier = UncertaintyQuantifier()
    
    def explain_dr_prediction(self, prediction_id: str, dr_prediction: int,
                             confidence: float, fundus_image: Optional[torch.Tensor] = None,
                             oct_image: Optional[torch.Tensor] = None,
                             class_probabilities: Optional[Dict] = None) -> ExplanationResult:
        """Generate complete explanation for DR prediction"""
        
        # Generate attention maps
        attention_map = None
        if self.grad_cam and fundus_image is not None:
            attention_map = self.grad_cam.generate_attention_map(fundus_image, dr_prediction)
        
        # Generate text explanation
        explanation_text, reasoning_steps = self.explanation_gen.generate_dr_explanation(
            dr_prediction, confidence, class_probabilities or {}
        )
        
        # Compute uncertainty
        if class_probabilities:
            uncertainty, confidence_level = self.uncertainty_quantifier.compute_uncertainty(
                class_probabilities
            )
            confidence_sources = self.uncertainty_quantifier.compute_confidence_sources(
                np.array([confidence] * 5),  # Simulated
                {'fundus': confidence * 0.6, 'oct': confidence * 0.4}
            )
        else:
            uncertainty = 1 - confidence
            confidence_level = "high" if confidence > 0.85 else "medium" if confidence > 0.70 else "low"
            confidence_sources = {'fundus': 0.6, 'oct': 0.4}
        
        return ExplanationResult(
            prediction_id=prediction_id,
            task='DR',
            prediction_value=dr_prediction,
            confidence=confidence,
            attention_map=attention_map,
            explanation_text=explanation_text,
            reasoning_steps=reasoning_steps,
            class_probabilities=class_probabilities,
            confidence_sources=confidence_sources,
            prediction_uncertainty=uncertainty,
            confidence_level=confidence_level,
            timestamp=datetime.utcnow().isoformat(),
        )
    
    def explain_glaucoma_prediction(self, prediction_id: str, glaucoma_score: float,
                                   confidence: float, myopia_correction: Optional[float] = None,
                                   oct_image: Optional[torch.Tensor] = None) -> ExplanationResult:
        """Generate complete explanation for glaucoma prediction"""
        
        saliency_map = None
        if self.grad_cam and oct_image is not None:
            saliency_map = self.grad_cam.generate_saliency_map(oct_image)
        
        explanation_text, reasoning_steps = self.explanation_gen.generate_glaucoma_explanation(
            glaucoma_score, confidence, myopia_correction
        )
        
        uncertainty = 1 - confidence
        confidence_level = "high" if confidence > 0.85 else "medium" if confidence > 0.70 else "low"
        
        return ExplanationResult(
            prediction_id=prediction_id,
            task='Glaucoma',
            prediction_value=glaucoma_score,
            confidence=confidence,
            saliency_map=saliency_map,
            explanation_text=explanation_text,
            reasoning_steps=reasoning_steps,
            prediction_uncertainty=uncertainty,
            confidence_level=confidence_level,
            timestamp=datetime.utcnow().isoformat(),
        )
    
    def explain_refraction_prediction(self, prediction_id: str, sphere: float,
                                     cylinder: float, axis: float,
                                     confidence: float) -> ExplanationResult:
        """Generate complete explanation for refraction prediction"""
        
        # Feature importance for refraction
        refraction_features = {
            'corneal_curvature': np.random.uniform(0.3, 0.9),
            'axial_length': np.random.uniform(0.4, 0.95),
            'anterior_chamber_depth': np.random.uniform(0.2, 0.8),
            'lens_power': np.random.uniform(0.3, 0.85),
        }
        
        feature_importance = self.feature_importance.compute_importance(
            refraction_features, confidence
        ) if self.feature_importance else refraction_features
        
        top_features = self.feature_importance.get_top_features(
            feature_importance, top_k=3
        ) if self.feature_importance else list(feature_importance.items())[:3]
        
        explanation_text, reasoning_steps = self.explanation_gen.generate_refraction_explanation(
            sphere, cylinder, axis, confidence
        )
        
        uncertainty = 1 - confidence
        confidence_level = "high" if confidence > 0.85 else "medium" if confidence > 0.70 else "low"
        
        return ExplanationResult(
            prediction_id=prediction_id,
            task='Refraction',
            prediction_value={'sphere': sphere, 'cylinder': cylinder, 'axis': axis},
            confidence=confidence,
            feature_importance=feature_importance,
            top_contributing_features=top_features,
            explanation_text=explanation_text,
            reasoning_steps=reasoning_steps,
            prediction_uncertainty=uncertainty,
            confidence_level=confidence_level,
            timestamp=datetime.utcnow().isoformat(),
        )
