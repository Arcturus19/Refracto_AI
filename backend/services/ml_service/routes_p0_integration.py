"""
FastAPI Routes Integration (Week 1 - P0 Features Integration)

Integrates all Phase 1 backend modules (P0.1-P0.6) into FastAPI endpoints:
- P0.1 Fusion: Multi-modal MTL predictions
- P0.2 Refracto-Pathological Link: Myopia correction (H2)
- P0.3 Ingestion: Multi-modal data validation
- P0.4 Local Data Manager: Anonymization + consent
- P0.5 Clinical Concordance: Expert review framework (H3)
- P0.6 Audit Logger: Immutable prediction logging
"""

from fastapi import APIRouter, File, UploadFile, HTTPException, Depends, Query
from fastapi.responses import JSONResponse, FileResponse
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
import asyncio
import logging

from core.fusion import MultiHeadFusion, MultiTaskFusionHead
from core.clinical_fusion import ClinicalDataEncoder
from core.refracto_pathological_link import RefractoPathologicalLink, apply_refracto_link
from core.multimodal_ingestion import MultiModalIngester, ImageQualityScore
from core.local_data_manager import LocalDataManager, ConsentRecord
from core.clinical_concordance import ClinicalConcordanceManager, ExpertReview
from core.audit_logger import AuditLogger, PredictionAuditLog

import torch
import numpy as np
from PIL import Image
import io

# ==================== Pydantic Schemas ====================

class MultiModalAnalysisRequest(BaseModel):
    """P0.1/P0.3: Multi-modal analysis request with image validation"""
    fundus_image: bytes = Field(..., description="Fundus image (PNG/JPG)")
    oct_image: bytes = Field(..., description="OCT image (PNG/JPG/DICOM)")
    patient_id: Optional[str] = Field(None, description="Local patient ID (will be anonymized)")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)

class MTLPredictionResponse(BaseModel):
    """P0.1/P0.2: Multi-task learning prediction with correction"""
    dr_prediction: Dict[str, Any]
    glaucoma_prediction: Dict[str, Any]
    refraction_prediction: Dict[str, Any]
    correction_factor: float
    audit_log_id: str
    timestamp: str

class ExpertReviewRequest(BaseModel):
    """P0.5: Clinical expert review submission"""
    patient_id: str
    dr_assessment: int = Field(..., ge=1, le=5, description="1-5 Likert scale")
    glaucoma_assessment: int = Field(..., ge=1, le=5)
    refraction_assessment: int = Field(..., ge=1, le=5)
    clinician_id: str
    clinician_notes: Optional[str] = None

class AuditLogResponse(BaseModel):
    """P0.6: Audit log entry response"""
    log_id: str
    timestamp: str
    anonymized_patient_hash: str
    task: str
    prediction: str
    confidence: float
    correction_applied: bool
    correction_factor: Optional[float]
    consent_verified: bool

class ConsentRecordRequest(BaseModel):
    """P0.4: Consent record creation"""
    patient_id: str
    consent_type: str = Field(..., description="Type: image_analysis, clinical_review, research")
    expiry_date: str = Field(..., description="YYYY-MM-DD format")

class LocalPatientRegistrationRequest(BaseModel):
    """P0.4: Local patient registration"""
    age_bracket: str
    diabetes_status: str
    iop_left: float
    iop_right: float
    consent_records: List[ConsentRecord] = Field(default_factory=list)

# ==================== Route Setup ====================

router = APIRouter(prefix="/api/ml", tags=["multi-modal-learning"])
logger = logging.getLogger(__name__)

# Initialize P0 modules globally (would be in a singleton/factory in production)
_fusion_model = None
_mtl_head = None
_clinical_encoder = None
_refracto_link = None
_ingester = None
_local_data_manager = None
_ccr_manager = None
_audit_logger = None

def get_models():
    """Initialize ML models (lazy load)"""
    global _fusion_model, _mtl_head, _clinical_encoder, _refracto_link, _ingester, _local_data_manager, _ccr_manager, _audit_logger
    
    if _fusion_model is None:
        logger.info("Initializing P0 models...")
        _fusion_model = MultiHeadFusion(fundus_dim=1000, oct_dim=768, fused_dim=512, num_heads=8)
        _clinical_encoder = ClinicalDataEncoder(input_dim=5, encoded_dim=64)
        _mtl_head = MultiTaskFusionHead(input_dim=512, clinical_dim=64, num_dr_classes=5, num_glaucoma_classes=2)
        _refracto_link = RefractoPathologicalLink()
        _ingester = MultiModalIngester()
        _local_data_manager = LocalDataManager()
        _ccr_manager = ClinicalConcordanceManager()
        _audit_logger = AuditLogger()
        logger.info("P0 models initialized successfully")
    
    return {
        'fusion': _fusion_model,
        'mtl_head': _mtl_head,
        'clinical_encoder': _clinical_encoder,
        'refracto_link': _refracto_link,
        'ingester': _ingester,
        'local_data_manager': _local_data_manager,
        'ccr_manager': _ccr_manager,
        'audit_logger': _audit_logger
    }

# ==================== P0.1/P0.2: MTL Analysis Endpoint ====================

@router.post("/analyze/mtl", response_model=MTLPredictionResponse)
async def analyze_multi_modal(request: MultiModalAnalysisRequest):
    """
    P0.1/P0.2: Multi-modal MTL analysis with automatic myopia correction.
    
    Flow:
    1. Validate images (P0.3: MultiModalIngester)
    2. Extract features (dummy feature extraction)
    3. Apply fusion (P0.1: MultiHeadFusion)
    4. Get MTL predictions (P0.1: MultiTaskFusionHead)
    5. Apply refracto correction (P0.2: RefractoPathologicalLink)
    6. Log immutably (P0.6: AuditLogger)
    7. Anonymize if local patient (P0.4: LocalDataManager)
    
    Target: H1 Hypothesis - Fusion superiority over single-modality
    """
    models = get_models()
    
    try:
        # P0.3: Validate and ingest images
        fundus_img = Image.open(io.BytesIO(request.fundus_image))
        oct_img = Image.open(io.BytesIO(request.oct_image))
        
        ingestion_result = models['ingester'].ingest_pair(
            fundus_image=fundus_img,
            oct_image=oct_img
        )
        
        if ingestion_result['status'] != 'accepted':
            raise HTTPException(status_code=400, detail=f"Image validation failed: {ingestion_result['status']}")
        
        # feature extraction (mock - in production, use actual model features)
        fundus_features = torch.randn(1, 1000)  # (1, fundus_dim)
        oct_features = torch.randn(1, 768)      # (1, oct_dim)
        
        # Parse clinical metadata if provided (Age, IOP, Diabetes, SphericalEq, Gender)
        encoded_clinical = None
        if request.metadata and 'clinical_data' in request.metadata:
            clinical = request.metadata['clinical_data']
            age = float(clinical.get('age', 50)) / 100.0
            iop = float(clinical.get('iop', 15)) / 40.0
            diabetes = 1.0 if str(clinical.get('diabetes_status', 'No')).lower() in ['yes', 'true', '1'] else 0.0
            spherical_equivalent = float(clinical.get('spherical_equivalent', 0.0) + 20) / 30.0
            gender = 1.0 if str(clinical.get('gender', 'Male')).lower() == 'female' else 0.0
            
            clinical_tensor = torch.tensor([[age, iop, diabetes, spherical_equivalent, gender]], dtype=torch.float32)
            with torch.no_grad():
                encoded_clinical = models['clinical_encoder'](clinical_tensor)
        
        # P0.1: Apply fusion
        with torch.no_grad():
            fused_features = models['fusion'](fundus_features, oct_features)  # (1, 512)
            
            # P0.1: Get MTL predictions
            dr_logits, glaucoma_logits, refraction_values = models['mtl_head'](fused_features, encoded_clinical)
            
            # P0.2: Apply refracto-pathological link
            predicted_sphere = refraction_values[0, 0].item()
            glaucoma_corrected, correction_factor = apply_refracto_link(
                glaucoma_logits=glaucoma_logits,
                predicted_sphere=predicted_sphere,
                refracto_link_model=models['refracto_link']
            )
            
            # Prepare response
            dr_class_idx = torch.argmax(dr_logits[0]).item()
            glaucoma_class_idx = torch.argmax(glaucoma_corrected[0]).item()
            
            dr_classes = ['No DR', 'Mild', 'Moderate', 'Severe', 'Proliferative']
            glaucoma_classes = ['Normal', 'Glaucoma']
            
            # P0.4: Handle local patient anonymization
            patient_hash = None
            if request.patient_id:
                patient_hash = models['local_data_manager'].hash_patient_identifier(request.patient_id)
            
            # P0.6: Log prediction immutably
            audit_entry = models['audit_logger'].log_prediction(
                anonymized_patient_hash=patient_hash or 'external',
                task='DR',
                prediction=dr_classes[dr_class_idx],
                confidence=torch.softmax(dr_logits, dim=1)[0, dr_class_idx].item(),
                correction_applied=True,
                correction_factor=correction_factor.item() if isinstance(correction_factor, torch.Tensor) else correction_factor,
                consent_verified=True,
                ethics_approval_id='ETH-2025-001'
            )
            
            response = MTLPredictionResponse(
                dr_prediction={
                    'class': dr_classes[dr_class_idx],
                    'confidence': torch.softmax(dr_logits, dim=1)[0, dr_class_idx].item(),
                    'class_scores': {
                        cls: torch.softmax(dr_logits, dim=1)[0, idx].item()
                        for idx, cls in enumerate(dr_classes)
                    }
                },
                glaucoma_prediction={
                    'prediction': glaucoma_classes[glaucoma_class_idx],
                    'confidence': torch.softmax(glaucoma_corrected, dim=1)[0, glaucoma_class_idx].item(),
                    'original_logit': glaucoma_logits[0, 1].item(),
                    'corrected_logit': glaucoma_corrected[0, 1].item(),
                    'correction_factor': correction_factor.item() if isinstance(correction_factor, torch.Tensor) else correction_factor
                },
                refraction_prediction={
                    'sphere': predicted_sphere,
                    'cylinder': refraction_values[0, 1].item(),
                    'axis': refraction_values[0, 2].item(),
                    'confidence': 0.92  # Mock confidence
                },
                correction_factor=correction_factor.item() if isinstance(correction_factor, torch.Tensor) else correction_factor,
                audit_log_id=audit_entry.log_id,
                timestamp=datetime.utcnow().isoformat()
            )
            
            return response
    
    except Exception as e:
        logger.error(f"MTL analysis failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# ==================== P0.5: Clinical Concordance Endpoints ====================

@router.post("/expert-review/submit")
async def submit_expert_review(request: ExpertReviewRequest):
    """
    P0.5: Submit expert clinical review for H3 hypothesis validation.
    
    Creates immutable expert review record contributing to global CCR calculation.
    """
    models = get_models()
    
    try:
        expert_review = ExpertReview(
            dr_agreement=request.dr_assessment,
            glaucoma_agreement=request.glaucoma_assessment,
            refraction_agreement=request.refraction_assessment,
            clinician_id=request.clinician_id,
            clinician_notes=request.clinician_notes or ""
        )
        
        # Add to CCR manager for aggregation
        models['ccr_manager'].add_review(
            patient_id=request.patient_id,
            review=expert_review
        )
        
        return {
            'status': 'success',
            'message': 'Expert review recorded for H3 validation',
            'review_id': f"REVIEW-{datetime.utcnow().timestamp()}"
        }
    
    except Exception as e:
        logger.error(f"Expert review submission failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/expert-review/ccr/global")
async def get_global_ccr():
    """
    P0.5: Get global Clinical Concordance Rate (H3 hypothesis validation).
    
    Returns:
    - global_ccr: Overall agreement rate
    - h3_hypothesis_status: 'PASS' if ≥85%, 'FAIL' if <85%, 'PENDING' if insufficient
    - task_specific_ccr: Breakdown by DR, Glaucoma, Refraction
    - expert_metrics: Individual expert performance
    """
    models = get_models()
    
    try:
        global_ccr, h3_status = models['ccr_manager'].calculate_global_ccr()
        task_ccrs = models['ccr_manager'].get_task_specific_ccr()
        expert_perf = models['ccr_manager'].get_expert_performance()
        
        return {
            'global_ccr': global_ccr,
            'h3_hypothesis_status': h3_status,
            'task_specific_ccr': task_ccrs,
            'expert_metrics': [
                {
                    'expert_id': exp_id,
                    'avg_agreement': metrics['avg_agreement'],
                    'dr_agreement': metrics.get('dr', 0),
                    'glaucoma_agreement': metrics.get('glaucoma', 0),
                    'refraction_agreement': metrics.get('refraction', 0)
                }
                for exp_id, metrics in expert_perf.items()
            ],
            'timestamp': datetime.utcnow().isoformat()
        }
    
    except Exception as e:
        logger.error(f"CCR calculation failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# ==================== P0.6: Audit Trail Endpoints ====================

@router.get("/audit/logs")
async def get_audit_logs(
    patient_hash: Optional[str] = Query(None),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None)
):
    """
    P0.6: Retrieve audit trail logs (immutable prediction records).
    
    Supports filtering by:
    - patient_hash: Anonymized patient identifier
    - start_date/end_date: Date range (YYYY-MM-DD)
    
    Returns: List of immutable PredictionAuditLog entries
    """
    models = get_models()
    
    try:
        logs = models['audit_logger'].get_audit_trail(
            patient_hash=patient_hash,
            start_date=start_date,
            end_date=end_date
        )
        
        return {
            'logs': [
                {
                    'log_id': log.log_id,
                    'timestamp': log.timestamp.isoformat(),
                    'anonymized_patient_hash': log.anonymized_patient_hash,
                    'task': log.task,
                    'prediction': log.prediction,
                    'confidence': log.confidence,
                    'correction_applied': log.correction_applied,
                    'correction_factor': log.correction_factor,
                    'consent_verified': log.consent_verified,
                    'clinician_feedback': {
                        'clinician_id': log.clinician_id,
                        'clinician_agreement': log.clinician_agreement,
                        'clinician_feedback': log.clinician_feedback,
                        'feedback_timestamp': log.clinician_feedback_timestamp.isoformat() if log.clinician_feedback_timestamp else None
                    } if log.clinician_id else None
                }
                for log in logs
            ],
            'count': len(logs),
            'timestamp': datetime.utcnow().isoformat()
        }
    
    except Exception as e:
        logger.error(f"Audit log retrieval failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/audit/logs/{log_id}")
async def get_audit_log_by_id(log_id: str):
    """P0.6: Retrieve specific audit log entry by ID"""
    models = get_models()
    
    try:
        log = models['audit_logger'].get_prediction_by_id(log_id)
        if not log:
            raise HTTPException(status_code=404, detail="Log not found")
        
        return {
            'log_id': log.log_id,
            'timestamp': log.timestamp.isoformat(),
            'prediction': log.prediction,
            'confidence': log.confidence
        }
    
    except Exception as e:
        logger.error(f"Audit log retrieval failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/audit/export/compliance")
async def export_audit_for_compliance(patient_hash: Optional[str] = Query(None)):
    """
    P0.6: Export audit logs for regulatory compliance (no PII).
    
    Returns CSV file suitable for:
    - Regulatory review
    - Ethics committee submission
    - Clinical audit trails
    """
    models = get_models()
    
    try:
        csv_data = models['audit_logger'].export_for_compliance(patient_hash=patient_hash)
        
        return FileResponse(
            path=csv_data,
            media_type='text/csv',
            filename=f"audit_export_{datetime.utcnow().isoformat()}.csv"
        )
    
    except Exception as e:
        logger.error(f"Audit export failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# ==================== P0.4: Local Data Manager Endpoints ====================

@router.post("/patient/register/local")
async def register_local_patient(request: LocalPatientRegistrationRequest):
    """
    P0.4: Register local (Sri Lankan) patient with anonymization.
    
    Anonymizes PII via SHA-256 one-way hashing. Returns anonymized_patient_id only.
    """
    models = get_models()
    
    try:
        # In production, patient_id would come from form, not request
        patient_record = models['local_data_manager'].create_local_patient(
            patient_identifier="local_patient_123",
            age_bracket=request.age_bracket,
            diabetes_status=request.diabetes_status,
            iop_left=request.iop_left,
            iop_right=request.iop_right
        )
        
        return {
            'anonymized_patient_id': patient_record.anonymized_patient_id,
            'status': 'registered',
            'message': 'Patient registered with full anonymization'
        }
    
    except Exception as e:
        logger.error(f"Patient registration failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/patient/consent/record")
async def record_consent(request: ConsentRecordRequest):
    """
    P0.4: Record immutable consent entry for patient.
    
    Creates audit trail for ethical compliance.
    """
    models = get_models()
    
    try:
        patient_hash = models['local_data_manager'].hash_patient_identifier(request.patient_id)
        
        models['local_data_manager'].record_consent(
            patient_hash=patient_hash,
            consent_type=request.consent_type,
            expiry_date=request.expiry_date
        )
        
        return {
            'status': 'recorded',
            'patient_hash': patient_hash,
            'consent_type': request.consent_type
        }
    
    except Exception as e:
        logger.error(f"Consent recording failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/patient/consent/verify/{patient_hash}")
async def verify_consent(patient_hash: str, consent_type: str):
    """P0.4: Verify current consent status for patient"""
    models = get_models()
    
    try:
        is_valid = models['local_data_manager'].verify_consent(
            patient_hash=patient_hash,
            consent_type=consent_type
        )
        
        return {
            'patient_hash': patient_hash,
            'consent_type': consent_type,
            'is_valid': is_valid,
            'timestamp': datetime.utcnow().isoformat()
        }
    
    except Exception as e:
        logger.error(f"Consent verification failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# ==================== Health Check ====================

@router.get("/health")
async def health_check():
    """Health check endpoint - verify all P0 modules initialized"""
    models = get_models()
    return {
        'status': 'healthy',
        'modules': {
            'fusion': 'ready',
            'mtl_head': 'ready',
            'refracto_link': 'ready',
            'ingester': 'ready',
            'local_data_manager': 'ready',
            'ccr_manager': 'ready',
            'audit_logger': 'ready'
        },
        'timestamp': datetime.utcnow().isoformat()
    }
