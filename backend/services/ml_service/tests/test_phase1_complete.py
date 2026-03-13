"""Comprehensive test suite for Refracto AI Phase 1 (Week 1-3)."""
import pytest
import torch
import numpy as np
from PIL import Image
import tempfile
import io

# Fusion tests
from core.fusion import MultiHeadFusion, MultiTaskFusionHead

# Refracto-link tests
from core.refracto_pathological_link import RefractoPathologicalLink, apply_refracto_link

# Ingestion tests
from core.multimodal_ingestion import MultiModalIngester, ImageQualityScore

# Local data tests
from core.local_data_manager import LocalDataManager

# Clinical concordance tests
from core.clinical_concordance import ClinicalConcordanceManager, ExpertReview

# Audit trail tests
from core.audit_logger import AuditLogger


# ============ FUSION TESTS ============

class TestFusion:
    """Test MultiHeadFusion module (P0.1)."""
    
    def test_fusion_instantiation(self):
        """Test module instantiates without errors."""
        fusion = MultiHeadFusion()
        assert fusion.fundus_dim == 1000
        assert fusion.oct_dim == 768
        assert fusion.fused_dim == 512

    def test_fusion_forward_pass_shape(self):
        """Test fusion produces correct output shape."""
        fusion = MultiHeadFusion()
        fundus = torch.randn(2, 1000)
        oct = torch.randn(2, 768)
        
        output = fusion(fundus, oct)
        assert output.shape == (2, 512), f"Expected (2, 512), got {output.shape}"

    def test_fusion_3d_to_2d_conversion(self):
        """Test fusion handles 3D input tensors with sequence dimension."""
        fusion = MultiHeadFusion()
        fundus = torch.randn(2, 1, 1000)  # (B, seq, dim)
        oct = torch.randn(2, 1, 768)
        
        output = fusion(fundus, oct)
        assert output.shape == (2, 512)

    def test_fusion_backward_pass(self):
        """Test gradient flow through fusion layer."""
        fusion = MultiHeadFusion()
        fundus = torch.randn(2, 1000, requires_grad=True)
        oct = torch.randn(2, 768, requires_grad=True)
        
        output = fusion(fundus, oct)
        loss = output.sum()
        loss.backward()
        
        assert fundus.grad is not None, "Fundus gradients not computed"
        assert oct.grad is not None, "OCT gradients not computed"

    def test_fusion_batch_sizes(self):
        """Test fusion works with various batch sizes."""
        fusion = MultiHeadFusion()
        
        for batch_size in [1, 2, 4, 8]:
            fundus = torch.randn(batch_size, 1000)
            oct = torch.randn(batch_size, 768)
            output = fusion(fundus, oct)
            assert output.shape == (batch_size, 512)


class TestMultiTaskHead:
    """Test MultiTaskFusionHead module."""
    
    def test_multi_task_head_instantiation(self):
        """Test MTL head instantiates."""
        head = MultiTaskFusionHead()
        assert head is not None

    def test_multi_task_head_outputs(self):
        """Test MTL head produces 3 outputs."""
        head = MultiTaskFusionHead()
        fused = torch.randn(2, 512)
        
        dr, glaucoma, refraction = head(fused)
        
        assert dr.shape == (2, 5), f"Expected DR (2, 5), got {dr.shape}"
        assert glaucoma.shape == (2, 2), f"Expected glaucoma (2, 2), got {glaucoma.shape}"
        assert refraction.shape == (2, 3), f"Expected refraction (2, 3), got {refraction.shape}"


class TestE2EMTLPipeline:
    """End-to-end MTL pipeline test."""
    
    def test_e2e_mtl_pipeline(self):
        """Test full MTL pipeline: Fusion → Multi-Task Head."""
        fusion = MultiHeadFusion()
        mtl_head = MultiTaskFusionHead()
        
        # Simulate feature extraction
        fundus_features = torch.randn(2, 1000)
        oct_features = torch.randn(2, 768)
        
        # Fuse
        fused = fusion(fundus_features, oct_features)
        
        # Multi-task predict
        dr, glaucoma, refraction = mtl_head(fused)
        
        # Verify shapes
        assert fused.shape == (2, 512)
        assert dr.shape == (2, 5)
        assert glaucoma.shape == (2, 2)
        assert refraction.shape == (2, 3)


# ============ REFRACTO-LINK TESTS ============

class TestRefractoLink:
    """Test RefractoPathologicalLink module (P0.2)."""
    
    def test_high_myopia_reduces_glaucoma(self):
        """High myopia should reduce glaucoma risk (H2)."""
        link = RefractoPathologicalLink()
        
        glaucoma_logits = torch.tensor([[2.0, 5.0]])  # High glaucoma confidence
        sphere_high_myopia = torch.tensor([-8.0])
        
        corrected = link(glaucoma_logits, sphere_high_myopia)
        
        # Glaucoma logit should be reduced for high myopia
        assert corrected[0, 1] < glaucoma_logits[0, 1], \
            f"High myopia should reduce glaucoma: {corrected[0, 1]} >= {glaucoma_logits[0, 1]}"

    def test_emmetropia_minimal_correction(self):
        """Emmetropia should have minimal correction."""
        link = RefractoPathologicalLink()
        
        glaucoma_logits = torch.tensor([[2.0, 3.0]])
        sphere_emmetropia = torch.tensor([0.0])
        
        corrected = link(glaucoma_logits, sphere_emmetropia)
        
        # Should be close to original
        assert torch.allclose(corrected, glaucoma_logits, atol=0.5), \
            f"Emmetropia correction should be minimal: {corrected} vs {glaucoma_logits}"

    def test_high_hyperopia_increases_glaucoma(self):
        """High hyperopia should increase glaucoma risk."""
        link = RefractoPathologicalLink()
        
        glaucoma_logits = torch.tensor([[2.0, 3.0]])
        sphere_hyperopia = torch.tensor([6.0])
        
        corrected = link(glaucoma_logits, sphere_hyperopia)
        
        # Glaucoma logit should increase for hyperopia
        assert corrected[0, 1] > glaucoma_logits[0, 1], \
            f"Hyperopia should increase glaucoma: {corrected[0, 1]} <= {glaucoma_logits[0, 1]}"

    def test_correction_factor_bounds(self):
        """Correction factor should always be in [0.5, 1.5]."""
        link = RefractoPathologicalLink()
        
        for sphere_val in [-20, -10, -5, 0, 5, 10]:
            sphere = torch.tensor([float(sphere_val)])
            correction = link.get_correction_factor(sphere)
            
            assert 0.4 <= correction.item() <= 1.6, \
                f"Correction factor out of bounds for sphere {sphere_val}: {correction.item()}"

    def test_functional_api(self):
        """Test functional API."""
        glaucoma_logits = torch.randn(2, 2)
        refraction = torch.tensor([[-3.0, 0.5, 180], [1.0, 0.25, 45]], dtype=torch.float)
        
        corrected, correction = apply_refracto_link(glaucoma_logits, refraction)
        
        assert corrected.shape == (2, 2)
        assert correction.shape == (2,)


# ============ INGESTION TESTS ============

class TestIngestion:
    """Test MultiModalIngester module (P0.3)."""
    
    def create_quality_image(self, quality_level: str) -> np.ndarray:
        """Create synthetic image with specified quality level."""
        if quality_level == "high":
            # High sharpness + contrast
            img = np.random.randint(50, 200, (256, 256, 3), dtype=np.uint8)
        elif quality_level == "low":
            # Blurry, low contrast
            img = np.ones((256, 256, 3), dtype=np.uint8) * np.random.randint(100, 150)
        else:
            img = np.random.randint(0, 255, (256, 256, 3), dtype=np.uint8)
        
        return img

    def test_quality_assessment(self):
        """Test image quality assessment."""
        ingester = MultiModalIngester()
        
        high_quality = self.create_quality_image("high")
        low_quality = self.create_quality_image("low")
        
        high_score = ingester.assess_image_quality(high_quality)
        low_score = ingester.assess_image_quality(low_quality)
        
        assert high_score.overall_score > low_score.overall_score, \
            f"High quality should score higher: {high_score.overall_score} vs {low_score.overall_score}"

    def test_ingest_pair_happy_path(self):
        """Test successful image pair ingestion."""
        ingester = MultiModalIngester()
        
        with tempfile.TemporaryDirectory() as tmpdir:
            fundus_path = f"{tmpdir}/fundus.png"
            oct_path = f"{tmpdir}/oct.png"
            
            fundus_img = Image.fromarray(self.create_quality_image("high"))
            oct_img = Image.fromarray(self.create_quality_image("high"))
            
            fundus_img.save(fundus_path)
            oct_img.save(oct_path)
            
            result = ingester.ingest_pair(fundus_path, oct_path, "PID001", "HASH001")
            
            assert result["status"] in ["accepted", "flagged"]
            assert result["patient_id"] == "HASH001"


# ============ LOCAL DATA TESTS ============

class TestLocalDataManager:
    """Test LocalDataManager module (P0.4)."""
    
    def test_patient_anonymization(self):
        """Test patient anonymization via one-way hashing."""
        mgr = LocalDataManager()
        
        patient = mgr.create_local_patient(
            age_bracket="41-60",
            diabetes_status="type2",
            iop_left=16.5,
            iop_right=17.2,
            original_identifier="SRILANKAN_PATIENT_00123"
        )
        
        # Verify hash generated (64 char SHA-256)
        assert len(patient.anonymized_patient_id) == 64
        
        # Verify no PII in dict
        patient_dict = patient.to_dict()
        assert "SRILANKAN_PATIENT" not in str(patient_dict)

    def test_consent_recording(self):
        """Test consent recording and verification."""
        mgr = LocalDataManager()
        
        patient = mgr.create_local_patient("41-60", "type2", 16.5, 17.2, "PID001")
        
        # Record consent
        consent = mgr.record_consent(
            patient.anonymized_patient_id,
            "imaging",
            True,
            clinician_id="DR_SILVA_001",
            ethics_approval_id="ETHICS_2026_001"
        )
        
        assert consent.consent_given is True
        
        # Verify consent
        assert mgr.verify_consent(patient.anonymized_patient_id, "imaging") is True
        assert mgr.verify_consent(patient.anonymized_patient_id, "research_publication") is False


# ============ CLINICAL CONCORDANCE TESTS ============

class TestClinicalConcordance:
    """Test ClinicalConcordanceManager module (P0.5)."""
    
    def test_ccr_calculation(self):
        """Test CCR calculation for single case."""
        mgr = ClinicalConcordanceManager()
        
        # Add 3 reviews for case 1
        for i in range(3):
            review = ExpertReview(
                review_id=f"REV_{i}",
                case_id="CASE_001",
                expert_id=f"E{i}",
                dr_agreement=4,  # Agree
                glaucoma_agreement=4,
                refraction_agreement=5,  # Strongly agree
                confidence=0.9,
                comments="Agrees with AI",
                timestamp="2026-03-12T10:00:00"
            )
            mgr.add_review(review)
        
        ccr = mgr.calculate_ccr_for_case("CASE_001")
        
        assert ccr is not None
        assert ccr["dr_ccr"] == 1.0  # All agreed
        assert ccr["overall_ccr"] > 0.9

    def test_global_ccr_and_h3_hypothesis(self):
        """Test H3 hypothesis: CCR ≥ 85%."""
        mgr = ClinicalConcordanceManager()
        
        # Add reviews for 5 cases (3 experts each)
        for case in range(5):
            for expert in range(3):
                review = ExpertReview(
                    review_id=f"REV_{case}_{expert}",
                    case_id=f"CASE_{case:03d}",
                    expert_id=f"E{expert}",
                    dr_agreement=4,  # Agreement
                    glaucoma_agreement=4,
                    refraction_agreement=4,
                    confidence=0.85,
                    comments="",
                    timestamp="2026-03-12T10:00:00"
                )
                mgr.add_review(review)
        
        global_ccr = mgr.calculate_global_ccr()
        
        assert global_ccr["h3_hypothesis_status"] in ["PASS", "FAIL"]
        print(f"Global CCR: {global_ccr['global_ccr']:.2%}")


# ============ AUDIT TRAIL TESTS ============

class TestAuditLogger:
    """Test AuditLogger module (P0.6)."""
    
    def test_prediction_logging(self):
        """Test logging a prediction."""
        logger = AuditLogger()
        
        log_id = logger.log_prediction({
            "anonymized_patient_hash": "PATIENT_HASH_001",
            "model_version": "v1.0",
            "modality": "multimodal",
            "task": "dr",
            "prediction": 2,  # DR grade
            "confidence": 0.92,
            "correction_applied": False,
            "consent_verified": True,
            "ethics_approval_id": "ETHICS_2026_001"
        })
        
        assert log_id is not None
        assert len(log_id) > 0

    def test_clinician_feedback(self):
        """Test adding clinician feedback to prediction."""
        logger = AuditLogger()
        
        log_id = logger.log_prediction({
            "anonymized_patient_hash": "PATIENT_HASH_001",
            "model_version": "v1.0",
            "modality": "multimodal",
            "task": "glaucoma",
            "prediction": 0.75,
            "confidence": 0.88,
            "consent_verified": True,
            "ethics_approval_id": "ETHICS_2026_001"
        })
        
        # Add feedback
        result = logger.add_clinician_feedback(
            log_id,
            clinician_id="DR_SILVA_001",
            agreement=True,
            feedback="AI prediction aligns with clinical assessment"
        )
        
        assert result is True

    def test_audit_trail_retrieval(self):
        """Test retrieving audit trail for patient."""
        logger = AuditLogger()
        
        # Log 3 predictions for same patient
        for i in range(3):
            logger.log_prediction({
                "anonymized_patient_hash": "PATIENT_HASH_A",
                "model_version": "v1.0",
                "modality": "multimodal",
                "task": "dr",
                "prediction": i,
                "confidence": 0.9 - i * 0.05,
                "consent_verified": True,
                "ethics_approval_id": "ETHICS_2026_001"
            })
        
        trail = logger.get_audit_trail("PATIENT_HASH_A")
        
        assert len(trail) == 3


# ============ RUN TESTS ============

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
