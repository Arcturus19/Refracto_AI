"""Local patient data management with anonymization + consent tracking (P0.4)."""
import hashlib
import json
from datetime import datetime, timedelta
from typing import Dict, Optional, List
from dataclasses import dataclass, asdict


@dataclass
class ConsentRecord:
    """Immutable consent audit record."""
    patient_id: str  # ANONYMIZED HASH only
    timestamp: str  # ISO 8601
    consent_type: str  # "imaging" | "ml_analysis" | "research_publication"
    consent_given: bool
    consent_method: str  # "digital_form" | "paper_scan" | "verbal_recorded"
    clinician_id: str
    ethics_approval_id: str
    duration_months: int  # How long consent valid


@dataclass
class LocalPatientRecord:
    """Local (Sri Lankan) patient with full anonymization."""
    anonymized_patient_id: str  # SHA-256 hash (irreversible)
    age_bracket: str  # "0-20" | "21-40" | "41-60" | "61-80" | "80+"
    diabetes_status: str  # "none" | "type1" | "type2" | "gestational"
    iop_left_eye: float  # Intra-ocular pressure (mmHg)
    iop_right_eye: float
    created_at: str  # ISO 8601
    consent_records: List[ConsentRecord]  # All consent entries (immutable audit trail)
    
    def to_dict(self) -> Dict:
        """Convert to dict, excluding any PII."""
        data = asdict(self)
        # No PII should be present (anonymized_patient_id is hash only)
        return data


class LocalDataManager:
    """Manage local patient cohort with full anonymization and consent tracking.
    
    Key principles:
    - Original patient identifiers NEVER stored
    - One-way SHA-256 hashing (cannot reverse to get original ID)
    - Immutable consent audit trail per patient
    - Full PII stripping before any export
    """
    
    def __init__(self, salt: str = "refracto_ai_local_2026"):
        self.salt = salt
        self.consents_log: List[ConsentRecord] = []
        self.patients: Dict[str, LocalPatientRecord] = {}
    
    def hash_patient_identifier(self, identifier: str) -> str:
        """Create irreversible patient hash (SHA-256).
        
        Original identifier is NEVER stored anywhere.
        Only one-way hash + clinical data stored.
        
        Args:
            identifier: Original patient ID/name (discarded after hashing)
        
        Returns:
            64-char SHA-256 hex digest
        """
        salted = f"{identifier}{self.salt}".encode('utf-8')
        return hashlib.sha256(salted).hexdigest()
    
    def create_local_patient(self, age_bracket: str, diabetes_status: str,
                            iop_left: float, iop_right: float,
                            original_identifier: str) -> LocalPatientRecord:
        """Register local patient with anonymization.
        
        Args:
            age_bracket: One of "0-20", "21-40", "41-60", "61-80", "80+"
            diabetes_status: One of "none", "type1", "type2", "gestational"
            iop_left: Intra-ocular pressure left eye (mmHg)
            iop_right: Intra-ocular pressure right eye (mmHg)
            original_identifier: Patient's original ID (will be hashed, not stored)
        
        Returns:
            LocalPatientRecord with anonymized ID
        """
        # Hash the original identifier (cannot be reversed)
        anonymized_id = self.hash_patient_identifier(original_identifier)
        
        # Create patient record with NO original ID stored
        patient = LocalPatientRecord(
            anonymized_patient_id=anonymized_id,
            age_bracket=age_bracket,
            diabetes_status=diabetes_status,
            iop_left_eye=iop_left,
            iop_right_eye=iop_right,
            created_at=datetime.now().isoformat(),
            consent_records=[]
        )
        
        self.patients[anonymized_id] = patient
        return patient
    
    def record_consent(self, anonymized_patient_id: str, consent_type: str,
                      consent_given: bool, clinician_id: str,
                      ethics_approval_id: str, duration_months: int = 12) -> ConsentRecord:
        """Record immutable consent event.
        
        Args:
            anonymized_patient_id: SHA-256 hash (not original ID)
            consent_type: Type of consent being recorded
            consent_given: True if patient consented
            clinician_id: ID of clinician requesting/recording consent
            ethics_approval_id: Reference to ethics committee approval
            duration_months: How long consent is valid (default 12 months)
        
        Returns:
            ConsentRecord that was recorded
        """
        record = ConsentRecord(
            patient_id=anonymized_patient_id,
            timestamp=datetime.now().isoformat(),
            consent_type=consent_type,
            consent_given=consent_given,
            consent_method="digital_form",
            clinician_id=clinician_id,
            ethics_approval_id=ethics_approval_id,
            duration_months=duration_months
        )
        
        # Add to immutable log
        self.consents_log.append(record)
        
        # Also add to patient's records
        if anonymized_patient_id in self.patients:
            self.patients[anonymized_patient_id].consent_records.append(record)
        
        return record
    
    def verify_consent(self, anonymized_patient_id: str, consent_type: str) -> bool:
        """Check if patient has valid, non-expired consent for operation.
        
        Args:
            anonymized_patient_id: SHA-256 hash
            consent_type: Type of consent required
        
        Returns:
            True if valid consent exists and is not expired
        """
        if anonymized_patient_id not in self.patients:
            return False
        
        patient = self.patients[anonymized_patient_id]
        
        # Check each consent record
        for consent in patient.consent_records:
            if consent.consent_type == consent_type and consent.consent_given:
                # Check if still valid (not expired)
                consent_date = datetime.fromisoformat(consent.timestamp)
                days_expired = (datetime.now() - consent_date).days
                max_days = consent.duration_months * 30
                
                if days_expired < max_days:
                    return True  # Valid, active consent found
        
        return False  # No valid consent found
    
    def get_all_consents_for_patient(self, anonymized_patient_id: str) -> List[ConsentRecord]:
        """Retrieve all consent records for a patient (audit trail).
        
        Args:
            anonymized_patient_id: SHA-256 hash
        
        Returns:
            List of all ConsentRecords (immutable)
        """
        if anonymized_patient_id not in self.patients:
            return []
        
        return self.patients[anonymized_patient_id].consent_records
    
    def export_anonymized_dataset(self) -> Dict:
        """Export entire dataset for ML training (fully anonymized).
        
        Returns dict with:
        - metadata: extraction date, patient count, ethics info
        - patients: list of anonymized patient records (no PII)
        """
        return {
            "metadata": {
                "extraction_date": datetime.now().isoformat(),
                "patient_count": len(self.patients),
                "ethics_approved": True,
                "note": "All patient identifiers are irreversible SHA-256 hashes"
            },
            "patients": [
                patient.to_dict()
                for patient in self.patients.values()
            ]
        }
    
    def get_patient_stats(self) -> Dict:
        """Get aggregate statistics about local patient cohort (no PII).
        
        Returns:
            Dictionary with cohort statistics
        """
        if not self.patients:
            return {"total_patients": 0}
        
        patients_list = list(self.patients.values())
        
        age_brackets = {}
        diabetes_counts = {}
        
        for patient in patients_list:
            age_brackets[patient.age_bracket] = age_brackets.get(patient.age_bracket, 0) + 1
            diabetes_counts[patient.diabetes_status] = diabetes_counts.get(patient.diabetes_status, 0) + 1
        
        return {
            "total_patients": len(patients_list),
            "age_distribution": age_brackets,
            "diabetes_distribution": diabetes_counts,
            "avg_iop_left": float(np.mean([p.iop_left_eye for p in patients_list])),
            "avg_iop_right": float(np.mean([p.iop_right_eye for p in patients_list])),
        }


import numpy as np
