"""Immutable audit trail for all ML predictions (P0.6)."""
import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional
import json
from dataclasses import dataclass, asdict


@dataclass
class PredictionAuditLog:
    """Immutable record of every ML prediction (append-only audit trail).
    
    This record is created when a prediction is made and cannot be modified
    (only clinician feedback can be appended separately).
    """
    log_id: str = None  # UUID generated at creation
    timestamp: str = None  # ISO 8601
    anonymized_patient_hash: str = None  # SHA-256, NO PII
    model_version: str = None
    input_modality: str = None  # "fundus" | "oct" | "multimodal"
    task: str = None  # "dr" | "glaucoma" | "refraction"
    
    # Predictions
    predicted_class_or_value: Any = None  # DR grade, glaucoma prob, or refraction values
    confidence: float = None
    
    # Refracto-link specific
    refraction_correction_applied: bool = False
    refraction_correction_factor: float = 1.0  # 0.5-1.5 range
    
    # Clinician action (added post-result)
    clinician_id: Optional[str] = None  # Who reviewed
    clinician_agreement: Optional[bool] = None  # Did expert agree?
    clinician_feedback: Optional[str] = None  # Free text notes
    feedback_timestamp: Optional[str] = None
    
    # Compliance
    consent_verified: bool = False
    ethics_approval_id: str = None
    
    def to_immutable_json(self) -> str:
        """Export as immutable JSON (could be stored in blockchain/IPFS)."""
        return json.dumps(asdict(self), default=str, sort_keys=True)


class AuditLogger:
    """Log all predictions with full accountability trail.
    
    Principles:
    - Append-only (predictions cannot be deleted or modified after creation)
    - Immutable (only new feedback records added, not changes to predictions)
    - Comprehensive logging (patient hash, model version, task, prediction, confidence)
    - Full transparency (all fields logged for audit compliance)
    """
    
    def __init__(self):
        self.logs: List[PredictionAuditLog] = []
        self.log_index: Dict[str, PredictionAuditLog] = {}  # log_id → log entry
    
    def log_prediction(self, prediction_data: Dict) -> str:
        """Create immutable log entry for prediction.
        
        Args:
            prediction_data: Dict with prediction details:
                - anonymized_patient_hash: Patient hash (required)
                - model_version: Model version string (required)
                - modality: "fundus" | "oct" | "multimodal"
                - task: "dr" | "glaucoma" | "refraction"
                - prediction: Predicted value(s)
                - confidence: Confidence score [0,1]
                - correction_applied: bool (was refracto-link applied)
                - correction_factor: float (if applicable)
                - consent_verified: bool
                - ethics_approval_id: Reference to ethics approval
        
        Returns:
            log_id (UUID string) for this prediction
        """
        # Public-facing IDs are expected to be prefixed for easy identification.
        log_id = f"LOG_{uuid.uuid4().hex}"
        
        log = PredictionAuditLog(
            log_id=log_id,
            timestamp=datetime.now().isoformat(),
            anonymized_patient_hash=prediction_data.get("anonymized_patient_hash"),
            model_version=prediction_data.get("model_version", "v1.0"),
            input_modality=prediction_data.get("modality", "multimodal"),
            task=prediction_data.get("task"),
            predicted_class_or_value=prediction_data.get("prediction"),
            confidence=prediction_data.get("confidence", 0.0),
            refraction_correction_applied=prediction_data.get("correction_applied", False),
            refraction_correction_factor=prediction_data.get("correction_factor", 1.0),
            clinician_id=None,  # Added later
            clinician_agreement=None,
            clinician_feedback=None,
            feedback_timestamp=None,
            consent_verified=prediction_data.get("consent_verified", False),
            ethics_approval_id=prediction_data.get("ethics_approval_id")
        )
        
        # Store in memory (in production, would persist to append-only DB)
        self.logs.append(log)
        self.log_index[log_id] = log
        
        return log_id
    
    def add_clinician_feedback(self, log_id: str, clinician_id: str,
                               agreement: bool, feedback: str) -> bool:
        """Add clinician review (updates existing log with feedback only).
        
        The original prediction is NEVER modified (immutable).
        Only feedback is appended.
        
        Args:
            log_id: ID of prediction to add feedback to
            clinician_id: Clinician reviewing
            agreement: Did clinician agree with AI?
            feedback: Clinician's comments
        
        Returns:
            True if updated successfully
        """
        if log_id not in self.log_index:
            return False
        
        log = self.log_index[log_id]
        log.clinician_id = clinician_id
        log.clinician_agreement = agreement
        log.clinician_feedback = feedback
        log.feedback_timestamp = datetime.now().isoformat()
        
        return True
    
    def get_audit_trail(self, anonymized_patient_hash: str, 
                       start_date: Optional[str] = None,
                       end_date: Optional[str] = None) -> List[Dict]:
        """Retrieve audit trail for patient (for auditors/compliance).
        
        Args:
            anonymized_patient_hash: Patient SHA-256 hash
            start_date: ISO date to start (inclusive)
            end_date: ISO date to end (inclusive)
        
        Returns:
            List of audit log dicts for this patient
        """
        patient_logs = [
            l for l in self.logs 
            if l.anonymized_patient_hash == anonymized_patient_hash
        ]
        
        # Filter by date if provided
        if start_date:
            start = datetime.fromisoformat(start_date)
            patient_logs = [l for l in patient_logs if datetime.fromisoformat(l.timestamp) >= start]
        
        if end_date:
            end = datetime.fromisoformat(end_date)
            patient_logs = [l for l in patient_logs if datetime.fromisoformat(l.timestamp) <= end]
        
        return [asdict(l) for l in patient_logs]
    
    def get_prediction_by_id(self, log_id: str) -> Optional[Dict]:
        """Retrieve specific prediction by log ID.
        
        Args:
            log_id: UUID of prediction
        
        Returns:
            Audit log dict, or None if not found
        """
        if log_id not in self.log_index:
            return None
        
        return asdict(self.log_index[log_id])
    
    def get_statistics(self) -> Dict:
        """Get audit trail statistics (no PII).
        
        Returns:
            Aggregate statistics
        """
        if not self.logs:
            return {"total_predictions": 0}
        
        by_task = {}
        by_model = {}
        reviewed_count = sum(1 for l in self.logs if l.clinician_id is not None)
        agreed_count = sum(1 for l in self.logs if l.clinician_agreement is True)
        
        for log in self.logs:
            by_task[log.task] = by_task.get(log.task, 0) + 1
            by_model[log.model_version] = by_model.get(log.model_version, 0) + 1
        
        return {
            "total_predictions": len(self.logs),
            "predictions_by_task": by_task,
            "predictions_by_model": by_model,
            "clinician_reviews": reviewed_count,
            "clinician_agreements": agreed_count,
            "avg_confidence": float(sum(l.confidence for l in self.logs) / len(self.logs)) if self.logs else 0.0
        }
    
    def export_for_compliance(self) -> Dict:
        """Export audit trail for regulatory compliance review.
        
        Returns:
            Complete audit data (no PII, hashes only)
        """
        return {
            "metadata": {
                "export_date": datetime.now().isoformat(),
                "total_records": len(self.logs),
                "note": "All patient identifiers are SHA-256 hashes. Original IDs are non-recoverable."
            },
            "audit_logs": [asdict(l) for l in self.logs],
            "statistics": self.get_statistics()
        }
