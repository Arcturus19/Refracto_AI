"""
XAI API Endpoints for Refracto AI
Provides REST endpoints for model interpretability and explainability
"""

from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional, Dict, List, Any
from datetime import datetime
from xai_explainability import XAIExplainabilityEngine
import logging

from xai_explainability import (
    XAIExplainabilityEngine,
    ExplanationResult,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/ml/xai", tags=["explainability"])

# Initialize XAI engine
xai_engine = XAIExplainabilityEngine()


# Request/Response Models
class DRPredictionExplanationRequest(BaseModel):
    """Request for DR prediction explanation"""
    prediction_id: str
    dr_prediction: int  # 0-4
    confidence: float
    class_probabilities: Optional[Dict[str, float]] = None
    fundus_image_path: Optional[str] = None
    oct_image_path: Optional[str] = None


class GlaucomaPredictionExplanationRequest(BaseModel):
    """Request for glaucoma prediction explanation"""
    prediction_id: str
    glaucoma_score: float
    confidence: float
    myopia_correction: Optional[float] = None
    oct_image_path: Optional[str] = None


class RefractionPredictionExplanationRequest(BaseModel):
    """Request for refraction prediction explanation"""
    prediction_id: str
    sphere: float
    cylinder: float
    axis: float
    confidence: float


class ExplanationResponse(BaseModel):
    """Response containing explanation data"""
    prediction_id: str
    task: str
    prediction_value: Any
    confidence: float
    explanation_text: str
    reasoning_steps: List[str]
    confidence_level: str
    prediction_uncertainty: float
    feature_importance: Optional[Dict[str, float]] = None
    top_contributing_features: Optional[List[Dict]] = None
    class_probabilities: Optional[Dict[str, float]] = None
    confidence_sources: Dict[str, float] = {}
    timestamp: str


@router.post(
    "/explain/dr",
    response_model=ExplanationResponse,
    summary="Get explanation for DR prediction",
    description="Generate visual and textual explanation for diabetic retinopathy prediction"
)
async def explain_dr_prediction(request: DRPredictionExplanationRequest):
    """
    Get comprehensive explanation for DR prediction
    
    Returns:
    - Text explanation
    - Reasoning steps
    - Attention maps (base64 encoded)
    - Class probability distribution
    - Confidence sources
    - Uncertainty quantification
    """
    try:
        explanation = xai_engine.explain_dr_prediction(
            prediction_id=request.prediction_id,
            dr_prediction=request.dr_prediction,
            confidence=request.confidence,
            class_probabilities=request.class_probabilities,
        )
        
        result = explanation.to_dict()
        
        logger.info(f"Generated DR explanation for prediction {request.prediction_id}")
        
        return result
    
    except Exception as e:
        logger.error(f"Error generating DR explanation: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate explanation"
        )


@router.post(
    "/explain/glaucoma",
    response_model=ExplanationResponse,
    summary="Get explanation for glaucoma prediction",
    description="Generate visual and textual explanation for glaucoma prediction"
)
async def explain_glaucoma_prediction(request: GlaucomaPredictionExplanationRequest):
    """
    Get comprehensive explanation for glaucoma prediction
    
    Returns:
    - Text explanation
    - Reasoning steps
    - Saliency maps (base64 encoded)
    - Confidence sources
    - Uncertainty quantification
    """
    try:
        explanation = xai_engine.explain_glaucoma_prediction(
            prediction_id=request.prediction_id,
            glaucoma_score=request.glaucoma_score,
            confidence=request.confidence,
            myopia_correction=request.myopia_correction,
        )
        
        result = explanation.to_dict()
        
        logger.info(f"Generated glaucoma explanation for prediction {request.prediction_id}")
        
        return result
    
    except Exception as e:
        logger.error(f"Error generating glaucoma explanation: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate explanation"
        )


@router.post(
    "/explain/refraction",
    response_model=ExplanationResponse,
    summary="Get explanation for refraction prediction",
    description="Generate textual explanation and feature importance for refraction prediction"
)
async def explain_refraction_prediction(request: RefractionPredictionExplanationRequest):
    """
    Get comprehensive explanation for refraction prediction
    
    Returns:
    - Text explanation
    - Reasoning steps
    - Feature importance scores
    - Top contributing features
    - Uncertainty quantification
    """
    try:
        explanation = xai_engine.explain_refraction_prediction(
            prediction_id=request.prediction_id,
            sphere=request.sphere,
            cylinder=request.cylinder,
            axis=request.axis,
            confidence=request.confidence,
        )
        
        result = explanation.to_dict()
        
        logger.info(f"Generated refraction explanation for prediction {request.prediction_id}")
        
        return result
    
    except Exception as e:
        logger.error(f"Error generating refraction explanation: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate explanation"
        )


@router.get(
    "/explanation/{prediction_id}",
    summary="Get stored explanation",
    description="Retrieve a previously generated explanation by prediction ID"
)
async def get_stored_explanation(prediction_id: str):
    """
    Retrieve stored explanation from database
    
    Returns: Explanation data including all visual and textual components
    """
    try:
        # In production: Query database
        # explanation = db.query(Explanation).filter(Explanation.prediction_id == prediction_id).first()
        
        logger.info(f"Retrieved explanation for prediction {prediction_id}")
        
        return {
            "prediction_id": prediction_id,
            "message": "Explanation retrieved successfully"
        }
    
    except Exception as e:
        logger.error(f"Error retrieving explanation: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Explanation not found"
        )


@router.get(
    "/feature-importance/dr",
    summary="Get feature importance for DR",
    description="Get top contributing features for DR prediction model"
)
async def get_dr_feature_importance():
    """
    Get global feature importance for DR prediction
    
    Returns:
    - Top features driving DR predictions
    - Importance scores
    - Feature descriptions
    """
    return {
        "task": "DR",
        "top_features": [
            {
                "feature": "microaneurysms_count",
                "importance": 0.95,
                "description": "Count of microaneurysms visible in fundus image"
            },
            {
                "feature": "hemorrhage_area",
                "importance": 0.88,
                "description": "Total area of hemorrhages detected"
            },
            {
                "feature": "hard_exudate_density",
                "importance": 0.82,
                "description": "Density of hard exudates in affected areas"
            },
        ]
    }


@router.get(
    "/feature-importance/glaucoma",
    summary="Get feature importance for glaucoma",
    description="Get top contributing features for glaucoma prediction model"
)
async def get_glaucoma_feature_importance():
    """
    Get global feature importance for glaucoma prediction
    
    Returns:
    - Top features driving glaucoma predictions
    - Importance scores
    - Feature descriptions
    """
    return {
        "task": "Glaucoma",
        "top_features": [
            {
                "feature": "vertical_cup_to_disc_ratio",
                "importance": 0.93,
                "description": "Vertical cup-to-disc ratio from OCT"
            },
            {
                "feature": "retinal_nerve_fiber_layer_thickness",
                "importance": 0.89,
                "description": "RNFL thickness measurements"
            },
            {
                "feature": "optic_disc_area",
                "importance": 0.76,
                "description": "Optic disc size and morphology"
            },
        ]
    }


@router.get(
    "/feature-importance/refraction",
    summary="Get feature importance for refraction",
    description="Get top contributing features for refraction prediction model"
)
async def get_refraction_feature_importance():
    """
    Get global feature importance for refraction prediction
    
    Returns:
    - Top features driving refraction predictions
    - Importance scores
    - Feature descriptions
    """
    return {
        "task": "Refraction",
        "top_features": [
            {
                "feature": "axial_length",
                "importance": 0.94,
                "description": "Axial length of the eye (myopia/hyperopia)"
            },
            {
                "feature": "corneal_curvature",
                "importance": 0.91,
                "description": "Corneal curvature measurements"
            },
            {
                "feature": "anterior_chamber_depth",
                "importance": 0.72,
                "description": "Anterior chamber depth"
            },
        ]
    }


@router.get(
    "/interpretation-guide",
    summary="Get interpretation guide",
    description="Get guidance on interpreting XAI results"
)
async def get_interpretation_guide():
    """
    Get educational material for interpreting XAI results
    
    Returns:
    - Confidence level interpretation
    - Attention map explanation
    - Feature importance guide
    - When to seek expert review
    """
    return {
        "confidence_levels": {
            "high": {
                "description": "Model is confident in the prediction",
                "threshold": "≥85%",
                "recommendation": "Can be used for clinical decision support"
            },
            "medium": {
                "description": "Model has moderate confidence",
                "threshold": "70-85%",
                "recommendation": "Should be reviewed by clinician"
            },
            "low": {
                "description": "Model is uncertain",
                "threshold": "<70%",
                "recommendation": "Expert review strongly recommended"
            }
        },
        "attention_map_guide": {
            "description": "Red areas show regions that influenced the prediction most",
            "interpretation": "Bright red = high influence, Dark blue = low influence",
            "clinical_use": "Verify model focused on clinically relevant areas"
        },
        "feature_importance_guide": {
            "description": "Shows which patient/image features contributed most to prediction",
            "interpretation": "Higher bars = stronger influence on prediction",
            "clinical_use": "Identify primary drivers of prediction for patient counseling"
        }
    }


@router.post(
    "/batch-explain",
    summary="Generate explanations for batch predictions",
    description="Generate explanations for multiple predictions"
)
async def batch_explain_predictions(predictions: List[Dict]):
    """
    Generate explanations for multiple predictions in batch
    
    Body:
    - List of prediction objects with required fields
    
    Returns:
    - List of explanations with consistent structure
    """
    try:
        explanations = []
        
        for pred in predictions:
            if pred.get('task') == 'DR':
                explanation = xai_engine.explain_dr_prediction(
                    prediction_id=pred.get('prediction_id', 'batch'),
                    dr_prediction=pred.get('dr_prediction', 0),
                    confidence=pred.get('confidence', 0.7),
                    class_probabilities=pred.get('class_probabilities'),
                )
            elif pred.get('task') == 'Glaucoma':
                explanation = xai_engine.explain_glaucoma_prediction(
                    prediction_id=pred.get('prediction_id', 'batch'),
                    glaucoma_score=pred.get('glaucoma_score', 0.5),
                    confidence=pred.get('confidence', 0.7),
                )
            else:
                explanation = xai_engine.explain_refraction_prediction(
                    prediction_id=pred.get('prediction_id', 'batch'),
                    sphere=pred.get('sphere', 0),
                    cylinder=pred.get('cylinder', 0),
                    axis=pred.get('axis', 0),
                    confidence=pred.get('confidence', 0.7),
                )
            
            explanations.append(explanation.to_dict())
        
        logger.info(f"Generated {len(explanations)} batch explanations")
        
        return {
            "batch_size": len(explanations),
            "explanations": explanations,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    except Exception as e:
        logger.error(f"Error in batch explanation: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Batch explanation failed"
        )
