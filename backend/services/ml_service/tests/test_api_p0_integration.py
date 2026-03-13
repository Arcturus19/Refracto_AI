"""
FastAPI Integration Tests (Week 1 - P0 Routes)

Tests all API endpoints:
- P0.1/P0.2: Multi-modal MTL analysis (/analyze/mtl)
- P0.3: Image ingestion + quality validation
- P0.4: Local patient registration + consent tracking
- P0.5: Expert review submission + CCR calculation
- P0.6: Audit log retrieval + compliance export

Run: pytest tests/test_api_p0_integration.py -v --cov=routes_p0_integration
"""

import pytest
from fastapi.testclient import TestClient
from datetime import datetime, timedelta
import json
import io
from PIL import Image

# Import FastAPI app (adjust path as needed)
from main import app

client = TestClient(app)

# ==================== Fixtures ====================

@pytest.fixture
def sample_fundus_image():
    """Create a sample fundus (color) image"""
    img = Image.new('RGB', (512, 512), color='red')
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format='PNG')
    return img_byte_arr.getvalue()

@pytest.fixture
def sample_oct_image():
    """Create a sample OCT (grayscale) image"""
    img = Image.new('L', (512, 512), color=128)
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format='PNG')
    return img_byte_arr.getvalue()

@pytest.fixture
def local_patient_data():
    """Sample local patient registration data"""
    return {
        'age_bracket': '45-50',
        'diabetes_status': 'Type 2',
        'iop_left': 15.2,
        'iop_right': 16.1,
        'consent_records': []
    }

# ==================== P0 Health Check ====================

class TestHealthCheck:
    def test_ml_service_health(self):
        """Verify all P0 modules initialized"""
        response = client.get('/api/ml/health')
        assert response.status_code == 200
        data = response.json()
        assert data['status'] == 'healthy'
        assert data['modules']['fusion'] == 'ready'
        assert data['modules']['mtl_head'] == 'ready'
        assert data['modules']['refracto_link'] == 'ready'
        assert data['modules']['ingester'] == 'ready'
        assert data['modules']['local_data_manager'] == 'ready'
        assert data['modules']['ccr_manager'] == 'ready'
        assert data['modules']['audit_logger'] == 'ready'

# ==================== P0.1/P0.2: MTL Analysis ====================

class TestMTLAnalysis:
    def test_mtl_analysis_success(self, sample_fundus_image, sample_oct_image):
        """P0.1/P0.2: Complete MTL analysis with refracto correction"""
        response = client.post(
            '/api/ml/analyze/mtl',
            json={
                'fundus_image': sample_fundus_image.hex(),  # Convert bytes to hex for JSON
                'oct_image': sample_oct_image.hex(),
                'patient_id': 'LOCAL_TEST_001',
                'metadata': {'session_id': 'test_session_1'}
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Validate DR prediction (P0.1)
        assert 'dr_prediction' in data
        assert data['dr_prediction']['class'] in ['No DR', 'Mild', 'Moderate', 'Severe', 'Proliferative']
        assert 0 <= data['dr_prediction']['confidence'] <= 1
        assert len(data['dr_prediction']['class_scores']) == 5
        
        # Validate Glaucoma prediction with correction (P0.1/P0.2)
        assert 'glaucoma_prediction' in data
        assert data['glaucoma_prediction']['prediction'] in ['Normal', 'Glaucoma']
        assert 0 <= data['glaucoma_prediction']['confidence'] <= 1
        assert 'correction_factor' in data['glaucoma_prediction']
        assert 0.5 <= data['glaucoma_prediction']['correction_factor'] <= 1.5
        
        # Validate Refraction prediction
        assert 'refraction_prediction' in data
        assert isinstance(data['refraction_prediction']['sphere'], float)
        assert isinstance(data['refraction_prediction']['cylinder'], float)
        assert isinstance(data['refraction_prediction']['axis'], float)
        
        # Validate audit logging (P0.6)
        assert 'audit_log_id' in data
        assert data['audit_log_id'].startswith('LOG_')
        
        # Verify correction factor recorded
        assert data['correction_factor'] == data['glaucoma_prediction']['correction_factor']

    def test_mtl_analysis_invalid_images(self):
        """P0.3: Reject invalid/corrupted images"""
        response = client.post(
            '/api/ml/analyze/mtl',
            json={
                'fundus_image': 'invalid_base64_data',
                'oct_image': 'another_invalid_data',
                'patient_id': 'LOCAL_TEST_002'
            }
        )
        
        assert response.status_code == 400
        assert 'validation' in response.json()['detail'].lower()

    def test_mtl_analysis_missing_image(self, sample_fundus_image):
        """P0.3: Reject incomplete multi-modal pair"""
        response = client.post(
            '/api/ml/analyze/mtl',
            json={
                'fundus_image': sample_fundus_image.hex(),
                'patient_id': 'LOCAL_TEST_003'
                # Missing OCT image
            }
        )
        
        assert response.status_code in [400, 422]

# ==================== P0.4: Patient Registration & Consent ====================

class TestLocalPatientManagement:
    def test_register_local_patient(self, local_patient_data):
        """P0.4: Register local patient with anonymization"""
        response = client.post(
            '/api/ml/patient/register/local',
            json=local_patient_data
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data['status'] == 'registered'
        assert 'anonymized_patient_id' in data
        # Verify anonymization (SHA-256 hash is 64 hex chars)
        assert len(data['anonymized_patient_id']) == 64
        assert all(c in '0123456789abcdef' for c in data['anonymized_patient_id'])

    def test_record_consent(self):
        """P0.4: Record immutable consent entry"""
        tomorrow = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
        
        response = client.post(
            '/api/ml/patient/consent/record',
            json={
                'patient_id': 'LOCAL_TEST_004',
                'consent_type': 'image_analysis',
                'expiry_date': tomorrow
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data['status'] == 'recorded'
        assert data['consent_type'] == 'image_analysis'
        assert 'patient_hash' in data

    def test_verify_consent_valid(self):
        """P0.4: Verify active consent"""
        # First record consent
        tomorrow = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
        client.post(
            '/api/ml/patient/consent/record',
            json={
                'patient_id': 'LOCAL_TEST_005',
                'consent_type': 'clinical_review',
                'expiry_date': tomorrow
            }
        )
        
        # Get patient hash (we'll use same hash logic)
        from ml_service.core.local_data_manager import LocalDataManager
        manager = LocalDataManager()
        patient_hash = manager.hash_patient_identifier('LOCAL_TEST_005')
        
        # Verify consent
        response = client.get(
            f'/api/ml/patient/consent/verify/{patient_hash}',
            params={'consent_type': 'clinical_review'}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data['is_valid'] == True

    def test_verify_consent_expired(self):
        """P0.4: Reject expired consent"""
        # Record expired consent
        yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
        response = client.post(
            '/api/ml/patient/consent/record',
            json={
                'patient_id': 'LOCAL_TEST_006',
                'consent_type': 'research',
                'expiry_date': yesterday
            }
        )
        
        if response.status_code == 200:
            from ml_service.core.local_data_manager import LocalDataManager
            manager = LocalDataManager()
            patient_hash = manager.hash_patient_identifier('LOCAL_TEST_006')
            
            # Verify consent - should be invalid
            response = client.get(
                f'/api/ml/patient/consent/verify/{patient_hash}',
                params={'consent_type': 'research'}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data['is_valid'] == False

# ==================== P0.5: Clinical Concordance & Expert Review ====================

class TestClinicalConcordance:
    def test_submit_expert_review_success(self):
        """P0.5: Submit expert clinical review"""
        response = client.post(
            '/api/ml/expert-review/submit',
            json={
                'patient_id': 'LOCAL_TEST_007',
                'dr_assessment': 4,
                'glaucoma_assessment': 5,
                'refraction_assessment': 4,
                'clinician_id': 'DR_SMITH_001',
                'clinician_notes': 'Good agreement with predictions'
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data['status'] == 'success'
        assert 'review_id' in data

    def test_submit_expert_review_invalid_likert(self):
        """P0.5: Reject invalid Likert scale values"""
        response = client.post(
            '/api/ml/expert-review/submit',
            json={
                'patient_id': 'LOCAL_TEST_008',
                'dr_assessment': 6,  # Invalid: should be 1-5
                'glaucoma_assessment': 3,
                'refraction_assessment': 4,
                'clinician_id': 'DR_JONES_001'
            }
        )
        
        assert response.status_code in [422, 400]

    def test_get_global_ccr(self):
        """P0.5: Calculate H3 global CCR"""
        # Submit multiple expert reviews first
        for i in range(5):
            client.post(
                '/api/ml/expert-review/submit',
                json={
                    'patient_id': f'LOCAL_TEST_{100+i}',
                    'dr_assessment': 4 + (i % 2),  # Vary between 4-5
                    'glaucoma_assessment': 4,
                    'refraction_assessment': 4,
                    'clinician_id': f'DR_{i:03d}'
                }
            )
        
        response = client.get('/api/ml/expert-review/ccr/global')
        
        assert response.status_code == 200
        data = response.json()
        assert 'global_ccr' in data
        assert 0 <= data['global_ccr'] <= 1
        assert data['h3_hypothesis_status'] in ['PASS', 'FAIL', 'PENDING']
        assert 'task_specific_ccr' in data
        assert 'expert_metrics' in data

    def test_h3_hypothesis_validation(self):
        """P0.5: Verify H3 status changes with CCR ≥85%"""
        # Submit reviews with high agreement (≥4)
        for i in range(20):
            client.post(
                '/api/ml/expert-review/submit',
                json={
                    'patient_id': f'H3_VALIDATION_{i}',
                    'dr_assessment': 5,  # Strongly agree
                    'glaucoma_assessment': 5,
                    'refraction_assessment': 4,
                    'clinician_id': f'DR_H3_{i:02d}'
                }
            )
        
        response = client.get('/api/ml/expert-review/ccr/global')
        data = response.json()
        
        # With high agreement, should approach 85%+ threshold
        if data['global_ccr'] >= 0.85:
            assert data['h3_hypothesis_status'] == 'PASS'

# ==================== P0.6: Audit Trail ====================

class TestAuditTrail:
    def test_get_audit_logs_all(self):
        """P0.6: Retrieve all audit logs"""
        response = client.get('/api/ml/audit/logs')
        
        assert response.status_code == 200
        data = response.json()
        assert 'logs' in data
        assert 'count' in data
        assert isinstance(data['logs'], list)

    def test_get_audit_logs_by_patient_hash(self):
        """P0.6: Filter audit logs by patient hash"""
        from ml_service.core.local_data_manager import LocalDataManager
        manager = LocalDataManager()
        patient_hash = manager.hash_patient_identifier('AUDIT_TEST_001')
        
        response = client.get(
            '/api/ml/audit/logs',
            params={'patient_hash': patient_hash}
        )
        
        assert response.status_code == 200
        data = response.json()
        # All returned logs should match patient hash
        for log in data['logs']:
            assert log['anonymized_patient_hash'] == patient_hash

    def test_get_audit_logs_by_date_range(self):
        """P0.6: Filter audit logs by date range"""
        start_date = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
        end_date = datetime.now().strftime('%Y-%m-%d')
        
        response = client.get(
            '/api/ml/audit/logs',
            params={
                'start_date': start_date,
                'end_date': end_date
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert 'logs' in data

    def test_get_audit_log_by_id(self):
        """P0.6: Retrieve specific audit log"""
        # First get a log ID
        response = client.get('/api/ml/audit/logs?limit=1')
        if response.status_code == 200 and response.json()['count'] > 0:
            log_id = response.json()['logs'][0]['log_id']
            
            response = client.get(f'/api/ml/audit/logs/{log_id}')
            assert response.status_code == 200
            data = response.json()
            assert data['log_id'] == log_id

    def test_audit_log_immutability(self):
        """P0.6: Verify audit logs are immutable (cannot DELETE/PATCH)"""
        # Try to DELETE an audit log
        response = client.delete('/api/ml/audit/logs/some_log_id')
        assert response.status_code in [405, 404]  # Method not allowed or not found
        
        # Try to PATCH an audit log
        response = client.patch(
            '/api/ml/audit/logs/some_log_id',
            json={'correction_applied': False}
        )
        assert response.status_code in [405, 404]

    def test_export_audit_compliance(self):
        """P0.6: Export audit logs for compliance (no PII)"""
        response = client.post('/api/ml/audit/export/compliance')
        
        assert response.status_code == 200
        assert response.headers['content-type'] == 'text/csv'
        assert 'audit_export_' in response.headers.get('content-disposition', '')

# ==================== Integration Tests ====================

class TestE2EIntegration:
    def test_full_workflow_local_patient(self, sample_fundus_image, sample_oct_image, local_patient_data):
        """E2E: Complete workflow for local Sri Lankan patient"""
        
        # Step 1: Register patient with anonymization (P0.4)
        reg_response = client.post(
            '/api/ml/patient/register/local',
            json=local_patient_data
        )
        assert reg_response.status_code == 200
        patient_id = reg_response.json()['anonymized_patient_id']
        
        # Step 2: Record consent (P0.4)
        tomorrow = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
        consent_response = client.post(
            '/api/ml/patient/consent/record',
            json={
                'patient_id': patient_id,
                'consent_type': 'image_analysis',
                'expiry_date': tomorrow
            }
        )
        assert consent_response.status_code == 200
        
        # Step 3: Submit multi-modal analysis (P0.1/P0.2/P0.3)
        mtl_response = client.post(
            '/api/ml/analyze/mtl',
            json={
                'fundus_image': sample_fundus_image.hex(),
                'oct_image': sample_oct_image.hex(),
                'patient_id': patient_id
            }
        )
        assert mtl_response.status_code == 200
        mtl_data = mtl_response.json()
        audit_log_id = mtl_data['audit_log_id']
        
        # Step 4: Submit expert review (P0.5)
        review_response = client.post(
            '/api/ml/expert-review/submit',
            json={
                'patient_id': patient_id,
                'dr_assessment': 4,
                'glaucoma_assessment': 4,
                'refraction_assessment': 5,
                'clinician_id': 'DR_E2E_001'
            }
        )
        assert review_response.status_code == 200
        
        # Step 5: Retrieve audit log (P0.6)
        audit_response = client.get(
            f'/api/ml/audit/logs/{audit_log_id}'
        )
        assert audit_response.status_code == 200
        audit_data = audit_response.json()
        assert audit_data['log_id'] == audit_log_id
        
        # Step 6: Check CCR (P0.5)
        ccr_response = client.get('/api/ml/expert-review/ccr/global')
        assert ccr_response.status_code == 200
        ccr_data = ccr_response.json()
        assert ccr_data['h3_hypothesis_status'] in ['PASS', 'FAIL', 'PENDING']
