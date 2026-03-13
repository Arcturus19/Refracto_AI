# Complete Refracto AI Phase 1 TODO List
**Research Project**: Hybrid XAI Clinical Decision Support System for Integrated Ophthalmic Care  
**Duration**: 4 Weeks (28 Days) | **Start**: March 12, 2026  
**Status**: Ready for Execution  

---

## 📋 Table of Completed Research Requirements

| Research Objective | P0 Features | Testing | Frontend | Timeline |
|-------------------|-----------|---------|----------|----------|
| O1: Hybrid MTL Architecture | P0.1, P0.2 | Unit + E2E | MTL Visualization | W1 |
| O2: Integrated Validation | P0.3, P0.4, P0.5 | Integration | Expert Review UI | W2-W3 |
| O3: Refracto-Path Link | P0.2 | Unit + Validation | Link Transparency | W1 |
| O4: XAI + Clinical Trust | P0.6 | Audit tests | Audit Dashboard | W3 |
| O5: Local Generalization | P0.4 | Consent tests | Consent Wizard | W2 |

---

# 🗓️ WEEK 1: FOUNDATION LAYER (MTL Architecture)

## Frontend Tasks — Week 1

### UX Enhancement 1.1: Multi-Modal Analysis Interface
- [ ] **Design**: Create figma mockup for multi-modal upload
  - Two side-by-side upload zones (Fundus + OCT)
  - Real-time image preview with quality indicators
  - Progress bars for each upload
- [ ] **Component**: Create `MultiModalUploader.tsx`
  - Drag-drop for both image types
  - File validation (size, format, dimensions)
  - Preview with metadata (filename, size, dimensions)
  - Quality badge (✓ Good / ⚠️ Check / ✗ Poor)
- [ ] **Hook**: Create `useMultiModalUpload.ts`
  - State management for both images
  - API integration: `POST /uploads/multimodal`
  - Error handling + retry logic
- [ ] **Testing**:
  - [ ] Test valid image pairs upload
  - [ ] Test invalid formats rejection
  - [ ] Test oversized file handling
  - [ ] Test quality feedback display
  - [ ] Test drag-drop functionality (unit + visual)

### UX Enhancement 1.2: MTL Results Display
- [ ] **Component**: Create `MTLResultsPanel.tsx` showing all 3 predictions
  - DR Grade card with color coding (0=green, 4=red)
  - Glaucoma Risk card with probability + correction factor
  - Refraction card (Sphere/Cylinder/Axis) with precision
  - Confidence scores for all tasks
  - Visual indicator: "Fusion Active ∞" badge
- [ ] **Sub-component**: Create `CorectionFactorTooltip.tsx`
  - Show myopia correction logic
  - Display input sphere value + correction calculation
  - Explain reduction/increase in glaucoma risk
  - Interactive (hover-triggered)
- [ ] **Testing**:
  - [ ] Test card rendering with all data types
  - [ ] Test tooltip triggers correctly
  - [ ] Test color coding logic (DR grades)
  - [ ] Test confidence score formatting
  - [ ] Test visual indicators update

### UX Enhancement 1.3: Navigation Redesign
- [ ] **Update**: Enhance `Sidebar.tsx` navigation
  - Add new route: `/analysis/mtl` (Multi-Modal Analysis)
  - Add new route: `/research/h1-fusion` (Hypothesis 1 validation)
  - Add research metrics dashboard link
  - Add pending items counter badge
- [ ] **Create**: Breadcrumb component
  - Show: Dashboard > Analysis > MTL > Results
  - Allow skip/jump between steps
- [ ] **Testing**:
  - [ ] Test all routes navigate correctly
  - [ ] Test breadcrumb updates on navigation
  - [ ] Test mobile responsive breadcrumb

---

## Backend Tasks — Week 1

### Backend 1.1: Multi-Modal Fusion Module (P0.1)
- [ ] **Create** `backend/services/ml_service/core/fusion.py`
  - [ ] Class: `MultiHeadFusion` (complete code from plan)
    - [ ] `__init__`: Initialize projections, attention, gate, norm
    - [ ] `forward()`: Input validation → projection → attention → gating → normalization
    - [ ] Test shape handling (2D and 3D tensors)
  - [ ] Class: `MultiTaskFusionHead` (complete code from plan)
    - [ ] Shared dense layers (512 → 256 → 128)
    - [ ] Task 1 head: DR (5 classes)
    - [ ] Task 2 head: Glaucoma (2 classes)
    - [ ] Task 3 head: Refraction (3 values regression)
  - [ ] Documentation: Docstrings + parameter descriptions
  - [ ] Review: Code style + PEP 8 compliance

### Backend 1.2: Refracto-Pathological Link Module (P0.2)
- [ ] **Create** `backend/services/ml_service/core/refracto_pathological_link.py`
  - [ ] Class: `RefractoPathologicalLink`
    - [ ] `normalize_sphere()`: Map sphere [-20, +10] → [-1, 1]
    - [ ] `forward()`: Apply correction curve to glaucoma logits
    - [ ] `get_correction_factor()`: Return correction only (for logging)
  - [ ] Function: `apply_refracto_link()`
    - Functional API for easy integration
  - [ ] Validation:
    - [ ] High myopia (sphere = -8) reduces glaucoma prob
    - [ ] Emmetropia (sphere = 0) minimal change
    - [ ] High hyperopia (sphere = +6) increases glaucoma prob
    - [ ] Correction factor always in [0.5, 1.5]

### Backend 1.3: Integration into Model Loader
- [ ] **Modify** `backend/services/ml_service/core/model_loader.py`
  - [ ] Add imports: `from fusion import MultiHeadFusion, MultiTaskFusionHead`
  - [ ] Add imports: `from refracto_pathological_link import RefractoPathologicalLink`
  - [ ] Add method: `_initialize_fusion_layer()`
    - Create fusion + MTL head instances
    - Handle GPU/CPU device placement
  - [ ] Add method: `predict_mtl(fundus_tensor, oct_tensor)`
    - Extract features from both backbones (no final classification)
    - Fuse: `fused = self.fusion(fundus_feat, oct_feat)`
    - Predict: `dr, glaucoma, refraction = self.mtl_head(fused)`
    - Apply link: `glaucoma_corrected = self.link(glaucoma, refraction[:, 0])`
    - Return dict with all predictions + correction factor
  - [ ] Backward compatibility: Keep existing `predict()` method unchanged

### Backend 1.4: New Endpoint for MTL Analysis
- [ ] **Modify** `backend/services/ml_service/main.py`
  - [ ] Add endpoint: `POST /analyze/mtl`
    - Input: Image file + patient_id (optional)
    - Process: Preprocess → model.predict_mtl() → apply link
    - Output: DR grade + confidence, Glaucoma prob + correction, Refraction values
    - Error handling: Validate image format + size
    - Logging: Use audit logger (P0.6 - but add hook now)
  - [ ] Add endpoint: `GET /model/mtl/info`
    - Return model version, fusion status, correction enabled flag
    - For frontend to verify MTL is active
  - [ ] Documentation: OpenAPI/Swagger updated with new endpoints

---

## Testing Tasks — Week 1

### Unit Tests: Fusion Module
- [ ] **Create** `backend/services/ml_service/tests/test_fusion.py`
  - [ ] Test `MultiHeadFusion` instantiation
  - [ ] Test forward pass shape (2, 1000) + (2, 768) → (2, 512)
  - [ ] Test gradient flow (backward pass)
  - [ ] Test with batch sizes: 1, 2, 4, 8
  - [ ] Test with 3D input tensors (with sequence dim)
  - [ ] Test gate mechanism: output between 0-1
  - [ ] Test norm layer: output normalized
  - [ ] Run: `pytest tests/test_fusion.py -v`
  - [ ] Coverage: Target >90%

### Unit Tests: Refracto-Link Module
- [ ] **Create** `backend/services/ml_service/tests/test_refracto_link.py`
  - [ ] Test sphere normalization: [-20, +10] → [-1, 1]
  - [ ] Test high myopia correction (sphere=-8 reduces glaucoma)
  - [ ] Test emmetropia correction (sphere=0 neutral)
  - [ ] Test hyperopia correction (sphere=+6 increases glaucoma)
  - [ ] Test correction factor bounds: 0.5 ≤ factor ≤ 1.5
  - [ ] Test edge cases: sphere=-20, sphere=+10
  - [ ] Test gradient flow for learnable curve
  - [ ] Run: `pytest tests/test_refracto_link.py -v`
  - [ ] Coverage: Target >85%

### Integration Tests: MTL Pipeline
- [ ] **Create** `backend/services/ml_service/tests/test_e2e_mtl.py`
  - [ ] Create dummy fundus image (256×256, RGB)
  - [ ] Create dummy OCT image (256×256, RGB)
  - [ ] Preprocess both images
  - [ ] Call `predict_mtl()` with both tensors
  - [ ] Verify output structure:
    - [ ] `dr_logits`: (1, 5)
    - [ ] `dr_label`: int [0-4]
    - [ ] `glaucoma_logits`: (1, 2)
    - [ ] `glaucoma_prob`: float [0-1]
    - [ ] `refraction`: (1, 3) for [sphere, cylinder, axis]
  - [ ] Apply refracto-link
  - [ ] Verify corrected glaucoma_logits
  - [ ] Verify correction_factor in [0.5, 1.5]
  - [ ] Run: `pytest tests/test_e2e_mtl.py -v`
  - [ ] Coverage: Target >80%

### API Tests: MTL Endpoint
- [ ] **Create** `backend/services/ml_service/tests/test_api_mtl.py`
  - [ ] Test `POST /analyze/mtl` endpoint
    - [ ] Valid image upload → 200 response
    - [ ] Response contains all 5 prediction fields
    - [ ] Invalid image format → 400 error
    - [ ] Missing file → 400 error
    - [ ] Oversized file → 413 error
  - [ ] Test `GET /model/mtl/info` endpoint
    - [ ] Returns model version
    - [ ] Returns fusion status (enabled/disabled)
    - [ ] Returns correction enabled flag
  - [ ] Test error responses: Clear error messages
  - [ ] Run: `pytest tests/test_api_mtl.py -v`

### Performance Tests: MTL
- [ ] **Create** `backend/services/ml_service/tests/test_performance_mtl.py`
  - [ ] Measure inference time (n=100 images)
    - [ ] Target: <300ms per image (CPU)
    - [ ] Target: <100ms per image (GPU if available)
  - [ ] Measure memory usage
    - [ ] Peak memory <2GB (CPU)
    - [ ] Peak memory <4GB (GPU)
  - [ ] Test memory leaks (1000 consecutive predictions)
  - [ ] Benchmark: Fusion layer alone vs. full MTL
  - [ ] Generate performance report

### Frontend Tests — Week 1
- [ ] **Unit Tests**: `src/components/MultiModalUploader.test.tsx`
  - [ ] Test component renders
  - [ ] Test file selection
  - [ ] Test image preview display
  - [ ] Test quality badge logic
  - [ ] Test error state rendering
  - Run: `npm test -- MultiModalUploader`

- [ ] **Unit Tests**: `src/components/MTLResultsPanel.test.tsx`
  - [ ] Test DR card rendering with all grades
  - [ ] Test color coding (0=green, 4=red)
  - [ ] Test glaucoma card display
  - [ ] Test refraction card display
  - [ ] Test correction factor tooltip
  - Run: `npm test -- MTLResultsPanel`

- [ ] **Integration Tests**: Navigation
  - [ ] Test route `/analysis/mtl` exists
  - [ ] Test breadcrumb updates
  - [ ] Test mobile responsive layout
  - Run: `npm test -- Sidebar`

---

## Research Validation — Week 1

### H1: Fusion Superiority Validation
- [ ] **Setup**: Benchmark dataset
  - [ ] Create test set: 50 paired fundus + OCT images
  - [ ] Manual labels for all: DR grade + Glaucoma
- [ ] **Baseline**: Single-modality models
  - [ ] Run Fundus-only model: Record AUC_DR, AUC_Glaucoma
  - [ ] Run OCT-only model: Record AUC_DR, AUC_Glaucoma
- [ ] **MTL Fusion**: Multi-modal model
  - [ ] Run MTL model: Record AUC_DR, AUC_Glaucoma
  - [ ] Calculate improvement: (MTL_AUC - max(Fundus_AUC, OCT_AUC)) / max(Fundus_AUC, OCT_AUC) * 100
  - [ ] Document: Expect >0% (validate fusion learn useful features)
- [ ] **Report**: `FUSION_VALIDATION_W1.md`
  - [ ] AUC comparisons (table)
  - [ ] Improvement percentages
  - [ ] Visualization: ROC curves (fusion vs. single-modality)

### H2: Refracto-Link Effectiveness Validation
- [ ] **Setup**: High-myopia patient subset
  - [ ] Filter test set: sphere < -6.0 (n ≥ 20)
  - [ ] Label ground truth: Glaucoma present? Yes/No
- [ ] **Baseline**: Without refracto-link
  - [ ] Run glaucoma predictions (raw logits)
  - [ ] Calculate FPR: False positives / All negatives
- [ ] **With Correction**: Refracto-link applied
  - [ ] Run glaucoma predictions + apply correction
  - [ ] Calculate FPR: False positives / All negatives
  - [ ] Calculate improvement: (FPR_baseline - FPR_corrected) / FPR_baseline * 100
  - [ ] Document: Expect ≥20% FPR reduction
- [ ] **Report**: `REFRACTO_LINK_W1.md`
  - [ ] FPR baseline vs. corrected (table)
  - [ ] Improvement percentage
  - [ ] Sphere vs. correction factor scatter plot

### Documentation: MTL Architecture
- [ ] **Create** `backend/services/ml_service/ARCHITECTURE_MTL_FINAL.md`
  - [ ] Table: MTL components + dimensions
  - [ ] Diagram: Data flow (Fundus → Fusion → DR/Glaucoma/Refraction)
  - [ ] Table: Hypothesis validation status
  - [ ] Section: Design decisions
  - [ ] Section: Known limitations
  - [ ] FAQ: Myopia correction explanation

---

## Week 1 Deliverables Checklist
- [ ] All unit tests passing (>90% coverage)
- [ ] All integration tests passing
- [ ] MTL endpoint live and tested
- [ ] Frontend components rendering correctly
- [ ] Fusion validation report completed
- [ ] Refracto-link validation report completed
- [ ] Architecture documentation complete
- [ ] **MERGE TO MAIN**: P0.1 + P0.2 code complete

---

---

# 🗓️ WEEK 2: DATA INFRASTRUCTURE

## Frontend Tasks — Week 2

### UX Enhancement 2.1: Multi-Modal Image Manager
- [ ] **Design**: Image gallery with filters
- [ ] **Component**: Create `ImageGalleryManager.tsx`
  - [ ] Display all uploaded patient images (Fundus + OCT)
  - [ ] Filter by: Image type, Date range, Quality score
  - [ ] Search by: Patient ID, Date
  - [ ] Pagination (20 per page)
  - [ ] Bulk select + delete
- [ ] **Sub-component**: `ImageCard.tsx`
  - [ ] Thumbnail preview
  - [ ] Image type badge (Fundus/OCT)
  - [ ] Quality score star rating (1-5)
  - [ ] Upload date + time
  - [ ] Quick actions: Preview, Delete, Move
- [ ] **Testing**:
  - [ ] Test gallery renders with 50+ images
  - [ ] Test filter functionality
  - [ ] Test search functionality
  - [ ] Test pagination
  - [ ] Test responsive layout (mobile)

### UX Enhancement 2.2: Local Patient Registration Wizard
- [ ] **Design**: Multi-step form for local patient onboarding
  - Step 1: Consent agreement (read + checkbox)
  - Step 2: Demographics (age bracket, diabetes status)
  - Step 3: Clinical data (IOP, eye measurements)
  - Step 4: Review + confirm anonymization
  - Step 5: Success screen (anonymized ID display)
- [ ] **Component**: Create `PatientRegistrationWizard.tsx`
  - [ ] Step indicator (1/5, 2/5, etc.)
  - [ ] Form validation at each step
  - [ ] Previous/Next navigation
  - [ ] Progress persistence (save on back)
  - [ ] Consent acceptance checkbox (required)
- [ ] **Sub-components**:
  - [ ] `ConsentAgreement.tsx`: Display consent text, checkbox, read time
  - [ ] `DemographicsForm.tsx`: Age bracket dropdown, diabetes select
  - [ ] `ClinicalDataForm.tsx`: IOP inputs (L/R), measurement date
  - [ ] `ReviewAndConfirm.tsx`: Show all data, anonymization explanation
  - [ ] `SuccessScreen.tsx`: Display anonymized hash, instructions
- [ ] **Testing**:
  - [ ] Test all 5 steps render correctly
  - [ ] Test form validation
  - [ ] Test wizard state persistence
  - [ ] Test navigation forward/backward
  - [ ] Test submit success/error handling
  - [ ] Mobile responsive test

### UX Enhancement 2.3: Image Quality Feedback UI
- [ ] **Component**: Create `ImageQualityIndicator.tsx`
  - [ ] Show quality metrics:
    - [ ] Sharpness score (0-1)
    - [ ] Contrast score (0-1)
    - [ ] Brightness score (0-1)
    - [ ] Overall score (0-1)
  - [ ] Color coding: Green (>0.8), Yellow (0.6-0.8), Red (<0.6)
  - [ ] Recommendations: "Image is blurry" / "Low contrast" / "Too dark/bright"
  - [ ] Allow reupload if quality low
- [ ] **Testing**:
  - [ ] Test quality score display
  - [ ] Test color coding logic
  - [ ] Test recommendations display
  - [ ] Test reupload button

### UX Enhancement 2.4: Enhanced Dashboard
- [ ] **Update**: `Dashboard.tsx`
  - [ ] Add section: "Local Patient Cohort" (n=50 enrolled)
  - [ ] Add section: "Data Quality Overview"
    - [ ] % of images passing quality threshold
    - [ ] Pie chart: Fundus vs. OCT count
  - [ ] Add section: "Ingestion Pipeline Status"
    - [ ] Pending: n images
    - [ ] Processed: n images
    - [ ] Rejected: n images (with reasons)
  - [ ] Add real-time stats update (5s polling)
- [ ] **Testing**:
  - [ ] Test new dashboard sections render
  - [ ] Test stats update correctly
  - [ ] Test charts load and display

---

## Backend Tasks — Week 2

### Backend 2.1: Multi-Modal Data Ingestion (P0.3)
- [ ] **Create** `backend/services/ml_service/core/multimodal_ingestion.py`
  - [ ] Class: `ImageQualityScore`
    - [ ] Fields: sharpness, contrast, brightness, overall_score
  - [ ] Class: `MultiModalIngester`
    - [ ] `assess_image_quality()`: Laplacian sharpness, histogram contrast, brightness
    - [ ] `load_dicom()`: Parse DICOM, normalize to RGB
    - [ ] `compute_feature_similarity()`: SIFT feature matching for co-registration
    - [ ] `ingest_pair()`: Full ingestion + validation
  - [ ] Error handling: Graceful failures for corrupted images

### Backend 2.2: Local Patient Data Manager (P0.4)
- [ ] **Create** `backend/services/patient_service/core/local_data_manager.py`
  - [ ] Class: `ConsentRecord` (dataclass)
  - [ ] Class: `LocalPatientRecord` (dataclass)
  - [ ] Class: `LocalDataManager`
    - [ ] `hash_patient_identifier()`: SHA-256 one-way hash
    - [ ] `create_local_patient()`: Register with anonymization
    - [ ] `record_consent()`: Immutable consent logging
    - [ ] `verify_consent()`: Check validity + expiry
    - [ ] `export_anonymized_dataset()`: Export (no PII)
  - [ ] Validation: No PII stored anywhere

### Backend 2.3: Database Schema Migration (P0.7)
- [ ] **Create** Migration: `add_local_data_schema.py`
  - [ ] Table: `local_patient`
    - [ ] Columns: id, anonymized_patient_id, age_bracket, diabetes_status, iop_left, iop_right, created_at
    - [ ] Index on anonymized_patient_id
  - [ ] Table: `consent_record`
    - [ ] Columns: id, anonymized_patient_id, timestamp, consent_type, consent_given, consent_method, clinician_id, ethics_approval_id, duration_months
    - [ ] FK to local_patient
    - [ ] Index on anonymized_patient_id, timestamp
  - [ ] Table: `image_pair`
    - [ ] Columns: id, anonymized_patient_id, fundus_file_path, oct_file_path, quality_score, coregistration_confidence, ingestion_date
    - [ ] FK to local_patient
  - [ ] Run migration: `alembic upgrade head`
  - [ ] Verify tables created

### Backend 2.4: New Endpoints for Local Data
- [ ] **Modify** `backend/services/patient_service/main.py`
  - [ ] `POST /local-patients/register`
    - Input: age_bracket, diabetes_status, iop_left, iop_right, original_identifier
    - Output: anonymized_patient_id
    - Logging: Create local patient record
  - [ ] `POST /local-patients/{patient_id}/consent`
    - Input: consent_type, consent_given, clinician_id, ethics_approval_id
    - Output: Consent record ID
    - Validation: Check ethics approval exists
  - [ ] `GET /local-patients/{patient_id}/consent-status`
    - Output: List of active consents + expiry dates
  - [ ] `GET /local-patients/stats`
    - Output: Total patients, avg age bracket, diabetes stats
    - No PII in response

### Backend 2.5: Ingestion Pipeline
- [ ] **Create** `backend/services/ml_service/ingestion_worker.py`
  - [ ] Function: `ingest_image_pair(fundus_path, oct_path, patient_id)`
    - Call MultiModalIngester
    - Validate quality + co-registration
    - Log result in database
    - Return: Success/Rejected + reason
  - [ ] Function: `batch_ingest_from_directory(dir_path)`
    - Scan for Fundus + OCT pairs
    - Match files by naming convention
    - Call `ingest_image_pair()` for each
    - Return: Summary (accepted, rejected, errors)
  - [ ] Error handling + retry logic

---

## Testing Tasks — Week 2

### Unit Tests: Multi-Modal Ingestion
- [ ] **Create** `backend/services/ml_service/tests/test_multimodal_ingestion.py`
  - [ ] Create synthetic test images (high/low quality)
  - [ ] Test `assess_image_quality()` with known quality levels
  - [ ] Verify high-quality score > low-quality score
  - [ ] Test `load_dicom()` with sample DICOM file
  - [ ] Test `compute_feature_similarity()` with matching/non-matching pairs
  - [ ] Test `ingest_pair()` acceptance/rejection logic
  - [ ] Test error handling: corrupted files, missing files
  - [ ] Run: `pytest tests/test_multimodal_ingestion.py -v`
  - [ ] Coverage: >85%

### Integration Tests: Local Data Manager
- [ ] **Create** `backend/services/patient_service/tests/test_local_data_manager.py`
  - [ ] Test patient registration + anonymization
  - [ ] Verify hash is one-way (cannot reverse)
  - [ ] Test consent recording
  - [ ] Test consent verification + expiry
  - [ ] Test PII not exposed in any output
  - [ ] Run: `pytest tests/test_local_data_manager.py -v`
  - [ ] Coverage: >90%

### Database Tests: Schema Migration
- [ ] **Create** `backend/services/patient_service/tests/test_db_migration.py`
  - [ ] Verify tables created: local_patient, consent_record, image_pair
  - [ ] Verify indexes created
  - [ ] Verify FK constraints
  - [ ] Test insert into local_patient (no errors)
  - [ ] Test insert into consent_record with valid FK
  - [ ] Test insert into image_pair with valid FK
  - [ ] Run: `pytest tests/test_db_migration.py -v`

### API Tests: Local Data Endpoints
- [ ] **Create** `backend/services/patient_service/tests/test_api_local_data.py`
  - [ ] Test `POST /local-patients/register`
    - [ ] Valid registration → 200, anonymized_id returned
    - [ ] Missing fields → 400 error
    - [ ] Verify DB insert
  - [ ] Test `POST /local-patients/{id}/consent`
    - [ ] Valid consent → 200, record ID returned
    - [ ] Invalid ethics_approval_id → 400 error
  - [ ] Test `GET /local-patients/{id}/consent-status`
    - [ ] Returns valid consents only
    - [ ] Excludes expired consents
  - [ ] Test `GET /local-patients/stats`
    - [ ] Returns aggregate stats (no PII)
  - [ ] Run: `pytest tests/test_api_local_data.py -v`

### Integration Tests: Full Ingestion Pipeline
- [ ] **Create** `backend/services/ml_service/tests/test_ingestion_pipeline.py`
  - [ ] Create 10 test image pairs (Fundus + OCT)
  - [ ] Register 10 local patients
  - [ ] Ingest all pairs
  - [ ] Verify accepted count
  - [ ] Verify rejected count + reasons
  - [ ] Verify database records created
  - [ ] Run: `pytest tests/test_ingestion_pipeline.py -v`

### Frontend Tests — Week 2
- [ ] **Unit Tests**: `ImageGalleryManager.test.tsx`
  - [ ] Test gallery renders 50+ images
  - [ ] Test filter by type
  - [ ] Test search functionality
  - [ ] Test pagination

- [ ] **Unit Tests**: `PatientRegistrationWizard.test.tsx`
  - [ ] Test all 5 steps render
  - [ ] Test form validation
  - [ ] Test navigation forward/backward
  - [ ] Test data persistence

- [ ] **Integration Tests**: Local Data Flow
  - [ ] Test patient registration → confirmation → list display

---

## Research Validation — Week 2

### Local Data Collection Checkpoint
- [ ] **Ethics Approval**: Confirm approval obtained
  - [ ] Document: `ETHICS_APPROVAL_LETTER.pdf`
  - [ ] Reference ID: `ETHICS_2026_001` (or actual)
- [ ] **Patient Enrollment**: Reach 50 local patients
  - [ ] Verify consent obtained for all
  - [ ] Verify anonymization complete
  - [ ] Verify no PII in database
- [ ] **Image Collection**: Reach 50 co-registered pairs
  - [ ] Verify quality: avg_quality_score > 0.7
  - [ ] Verify co-registration: confidence > 0.6
  - [ ] Verify ingestion pipeline working
- [ ] **Report**: `LOCAL_DATA_COLLECTION_W2.md`
  - [ ] Patient count: 50
  - [ ] Image pairs count: 50
  - [ ] Quality metrics (avg, min, max)
  - [ ] Screenshots of dashboard stats

### Documentation: Local Data Management
- [ ] **Create** `ETHICAL_DATA_MANAGEMENT.md`
  - [ ] Anonymization approach
  - [ ] Consent workflow
  - [ ] Data storage architecture
  - [ ] Access controls
  - [ ] Audit trail for local data

---

## Week 2 Deliverables Checklist
- [ ] P0.3 (Ingestion) code complete + tested
- [ ] P0.4 (Local Data Manager) code complete + tested
- [ ] Database migration executed + verified
- [ ] 50+ local patients registered
- [ ] 50+ image pairs ingested
- [ ] Frontend: Image gallery, patient wizard, quality indicators
- [ ] All tests passing (>85% coverage)
- [ ] Ethics approval documentation
- [ ] **MERGE TO MAIN**: P0.3 + P0.4 code complete

---

---

# 🗓️ WEEK 3: VALIDATION & COMPLIANCE

## Frontend Tasks — Week 3

### UX Enhancement 3.1: Clinical Concordance Review Panel (P0.5)
- [ ] **Design**: Expert review interface with Likert scales
- [ ] **Component**: Create `ClinicalConcordancePanel.tsx`
  - [ ] Display AI predictions (read-only)
  - [ ] Display XAI heatmap (read-only)
  - [ ] Three Likert scale questions:
    - [ ] "DR severity assessment agreement" (1-5)
    - [ ] "Glaucoma risk assessment agreement" (1-5)
    - [ ] "Refraction accuracy agreement" (1-5)
  - [ ] Expert confidence slider (0-1)
  - [ ] Comments text area (optional)
  - [ ] Submit + Next Case button
  - [ ] Review count display (e.g., "Reviewed 5/20 cases")
- [ ] **Sub-components**:
  - [ ] `LikertScale.tsx`: Reusable 1-5 scale
  - [ ] `CCRProgressBar.tsx`: Visual progress indicator
  - [ ] `CCRMetrics.tsx`: Display current CCR values (updated in real-time)
- [ ] **Testing**:
  - [ ] Test Likert scales interactive
  - [ ] Test form validation (all fields required)
  - [ ] Test progress bar updates
  - [ ] Test metrics display + calculation

### UX Enhancement 3.2: Audit Trail Dashboard
- [ ] **Design**: Timeline view of all predictions + clinician actions
- [ ] **Component**: Create `AuditTrailDashboard.tsx`
  - [ ] Filter options: Date range, Patient, Task type, Clinician
  - [ ] Timeline display with cards:
    - [ ] Timestamp
    - [ ] Anonymized patient hash
    - [ ] Prediction (DR/Glaucoma/Refraction)
    - [ ] Confidence score
    - [ ] Clinician review status (pending/reviewed/agreed/disagreed)
    - [ ] Clinician feedback (if any)
  - [ ] Export timeline as CSV
  - [ ] Pagination (50 per page)
- [ ] **Sub-components**:
  - [ ] `AuditCard.tsx`: Individual audit entry
  - [ ] `FilterPanel.tsx`: Date/patient/task filter
  - [ ] `ExportButton.tsx`: CSV export
- [ ] **Testing**:
  - [ ] Test timeline renders 50+ entries
  - [ ] Test filters work correctly
  - [ ] Test CSV export
  - [ ] Test pagination

### UX Enhancement 3.3: XAI Explanation Viewer
- [ ] **Component**: Create `XAIExplanationViewer.tsx`
  - [ ] Display prediction + Grad-CAM heatmap (left)
  - [ ] Display explanation text (right)
  - [ ] Show SHAP values (if available) in table
  - [ ] Interactive: Hover on image → highlight SHAP region
  - [ ] Toggle between Grad-CAM + SHAP views
  - [ ] Zoom controls on heatmap
- [ ] **Sub-components**:
  - [ ] `HeatmapViewer.tsx`: Image + overlay with zoom
  - [ ] `SHAPTable.tsx`: Feature importance table
  - [ ] `ExplanationText.tsx`: Natural language reasoning
- [ ] **Testing**:
  - [ ] Test image + heatmap rendering
  - [ ] Test toggle between views
  - [ ] Test zoom functionality
  - [ ] Test hover interactions

### UX Enhancement 3.4: Research Metrics Dashboard
- [ ] **Component**: Create `ResearchMetricsDashboard.tsx`
  - [ ] Display H1, H2, H3 hypothesis status
  - [ ] Section 1: Fusion Validation
    - [ ] MTL AUC vs. Single-modality AUC (bar chart)
    - [ ] Improvement percentage
  - [ ] Section 2: Refracto-Link Validation
    - [ ] FPR baseline vs. corrected (bar chart)
    - [ ] Improvement percentage
  - [ ] Section 3: Clinical Concordance
    - [ ] Global CCR (large metric display)
    - [ ] CCR status badge (PASS if ≥85%)
    - [ ] Breakdown by task (DR CCR, Glaucoma CCR, Refraction CCR)
  - [ ] Data source: Real-time from API
- [ ] **Testing**:
  - [ ] Test all metrics display correctly
  - [ ] Test charts render
  - [ ] Test data updates from API

---

## Backend Tasks — Week 3

### Backend 3.1: Clinical Concordance Framework (P0.5)
- [ ] **Create** `backend/services/ml_service/core/clinical_concordance.py`
  - [ ] Class: `ExpertReview` (dataclass)
  - [ ] Class: `ClinicalConcordanceManager`
    - [ ] `add_review()`: Record expert review
    - [ ] `calculate_ccr_for_case()`: Single case CCR
    - [ ] `calculate_global_ccr()`: All cases CCR (H3 validation)
- [ ] **Create** DB table migration:
  - [ ] Table: `expert_review`
    - Columns: id, case_id, expert_id, dr_agreement (1-5), glaucoma_agreement (1-5), refraction_agreement (1-5), confidence (0-1), comments, timestamp

### Backend 3.2: Ethical Audit Trail (P0.6)
- [ ] **Create** `backend/services/ml_service/core/audit_logger.py`
  - [ ] Class: `PredictionAuditLog` (dataclass)
    - [ ] Fields: log_id, timestamp, anonymized_patient_hash, model_version, prediction, confidence, clinician_action, feedback, ethics_approval_id
  - [ ] Class: `AuditLogger`
    - [ ] `log_prediction()`: Create immutable audit entry
    - [ ] `add_clinician_feedback()`: Add review post-result
    - [ ] `get_audit_trail()`: Retrieve for patient/time range
- [ ] **Create** DB table migration:
  - [ ] Table: `prediction_audit_log`
    - Columns: id, log_id, timestamp, anonymized_patient_hash, model_version, task, prediction, confidence, correction_applied, correction_factor, clinician_id, clinician_agreement, feedback, consent_verified, ethics_approval_id
    - Indexes: anonymized_patient_hash, timestamp
    - Add: Append-only constraint (no UPDATE allowed)

### Backend 3.3: New Endpoints for Validation
- [ ] **Modify** `backend/services/ml_service/main.py`
  - [ ] `POST /expert-review/add`
    - Input: case_id, expert_id, dr_agreement, glaucoma_agreement, refraction_agreement, confidence, comments
    - Output: review_id
    - Call: `ccr_manager.add_review()`
  - [ ] `GET /expert-review/ccr/global`
    - Output: global_ccr, h3_status (PASS/FAIL), case_count, case_details
    - Call: `ccr_manager.calculate_global_ccr()`
  - [ ] `GET /expert-review/ccr/case/{case_id}`
    - Output: case_ccr, reviewer_count, task_breakdown
  - [ ] `POST /audit/log`
    - Input: prediction_data
    - Output: log_id
    - Call: `audit_logger.log_prediction()`
  - [ ] `GET /audit/trail/{patient_hash}`
    - Output: List of audit entries for patient
    - Call: `audit_logger.get_audit_trail()`
  - [ ] `POST /audit/feedback/{log_id}`
    - Input: clinician_id, agreement, feedback
    - Output: Success
    - Call: `audit_logger.add_clinician_feedback()`

### Backend 3.4: Integration with Prediction Pipeline
- [ ] **Modify** `backend/services/ml_service/main.py` `/analyze/mtl` endpoint
  - [ ] After prediction, call: `audit_logger.log_prediction()`
  - [ ] Pass: anonymized_patient_hash, prediction, confidence, correction_applied, consent_verified
  - [ ] Return: prediction + log_id (for frontend)
  - [ ] Handle logging errors gracefully (don't fail prediction)

---

## Testing Tasks — Week 3

### Unit Tests: Clinical Concordance
- [ ] **Create** `backend/services/ml_service/tests/test_clinical_concordance.py`
  - [ ] Test ExpertReview dataclass
  - [ ] Test `add_review()`
  - [ ] Test `calculate_ccr_for_case()` with mock reviews
  - [ ] Test CCR calculation logic: (agreements ≥4) / total
  - [ ] Test `calculate_global_ccr()` with multiple cases
  - [ ] Test H3 hypothesis detection: CCR ≥ 0.85 → PASS
  - [ ] Run: `pytest tests/test_clinical_concordance.py -v`
  - [ ] Coverage: >90%

### Unit Tests: Audit Trail
- [ ] **Create** `backend/services/ml_service/tests/test_audit_logger.py`
  - [ ] Test PredictionAuditLog dataclass
  - [ ] Test `log_prediction()` creates entry
  - [ ] Test `add_clinician_feedback()` updates without overwriting
  - [ ] Test `get_audit_trail()` retrieves correct entries
  - [ ] Test immutability: entries cannot be deleted
  - [ ] Run: `pytest tests/test_audit_logger.py -v`
  - [ ] Coverage: >85%

### Database Tests: Audit Trail Schema
- [ ] **Create** `backend/services/ml_service/tests/test_audit_db.py`
  - [ ] Verify table created: prediction_audit_log
  - [ ] Verify append-only constraint
  - [ ] Verify indexes on patient_hash + timestamp
  - [ ] Test insert audit entry
  - [ ] Test query by patient_hash
  - [ ] Test query by date range
  - [ ] Run: `pytest tests/test_audit_db.py -v`

### API Tests: Concordance + Audit Endpoints
- [ ] **Create** `backend/services/ml_service/tests/test_api_ccr_audit.py`
  - [ ] Test `POST /expert-review/add` → 200
  - [ ] Test `GET /expert-review/ccr/global` → returns CCR
  - [ ] Test `GET /expert-review/ccr/case/{id}` → returns case CCR
  - [ ] Test `POST /audit/log` → returns log_id
  - [ ] Test `GET /audit/trail/{hash}` → returns entries
  - [ ] Test `POST /audit/feedback/{id}` → updates successfully
  - [ ] Run: `pytest tests/test_api_ccr_audit.py -v`

### Integration Tests: Full Prediction + Audit + CCR Flow
- [ ] **Create** `backend/services/ml_service/tests/test_e2e_audit_ccr.py`
  - [ ] Register patient → get anonymized hash
  - [ ] Run MTL prediction → log created
  - [ ] Verify audit entry in DB
  - [ ] Add 5 expert reviews → CCR calculated
  - [ ] Verify CCR ≥ 0.85 (or document actual value)
  - [ ] Retrieve audit trail → all entries present
  - [ ] Run: `pytest tests/test_e2e_audit_ccr.py -v`

### Frontend Tests — Week 3
- [ ] **Unit Tests**: `ClinicalConcordancePanel.test.tsx`
  - [ ] Test Likert scales render
  - [ ] Test form submission
  - [ ] Test CCR metrics update

- [ ] **Unit Tests**: `AuditTrailDashboard.test.tsx`
  - [ ] Test timeline renders 50+ entries
  - [ ] Test filters
  - [ ] Test CSV export

- [ ] **Unit Tests**: `XAIExplanationViewer.test.tsx`
  - [ ] Test heatmap display
  - [ ] Test SHAP table
  - [ ] Test view toggle

- [ ] **Unit Tests**: `ResearchMetricsDashboard.test.tsx`
  - [ ] Test H1/H2/H3 status display
  - [ ] Test chart rendering

---

## Research Validation — Week 3

### H1: Fusion Superiority (Update from W1)
- [ ] **Validation**: Add 50 more test images
  - [ ] Run MTL model: Update AUC
  - [ ] Update improvement percentage
  - [ ] Document: H1 validated if improvement ≥3%
- [ ] **Report**: `FUSION_VALIDATION_W3_FINAL.md`

### H2: Refracto-Link (Update from W1)
- [ ] **Validation**: Add high-myopia patient subset from local data
  - [ ] Recalculate FPR with local data
  - [ ] Update improvement percentage
  - [ ] Document: H2 validated if FPR reduction ≥20%
- [ ] **Report**: `REFRACTO_LINK_W3_FINAL.md`

### H3: Clinical Concordance Rate (NEW - Core W3 validation)
- [ ] **Expert Panel Recruitment**:
  - [ ] Recruit 3–5 ophthalmologists
  - [ ] Conduct training on CCR interface (1 hour)
  - [ ] Provide 20 test cases for each expert
- [ ] **Expert Review Session**:
  - [ ] Each expert reviews 20 cases (1-5 scales for 3 tasks)
  - [ ] Expert provides confidence score + comments
  - [ ] System calculates CCR in real-time
- [ ] **H3 Validation**:
  - [ ] Calculate global CCR = (agreements ≤4) / total
  - [ ] Status: PASS if CCR ≥ 0.85; otherwise FAIL
  - [ ] Document: All three experts' individual CCRs + global
- [ ] **Report**: `H3_CLINICAL_CONCORDANCE_W3.md`
  - [ ] Table: Expert-by-expert CCR breakdown
  - [ ] Table: Task-by-task CCR (DR vs. Glaucoma vs. Refraction)
  - [ ] Analysis: Which cases had low concordance? Why?
  - [ ] Conclusion: H3 PASS/FAIL with justification

### Documentation: Audit & Compliance
- [ ] **Create** `AUDIT_TRAIL_DOCUMENTATION.md`
  - [ ] Audit log schema + sample entries
  - [ ] How to query audit trail
  - [ ] Cleansing schedule (if needed)
  - [ ] Compliance references (GDPR, local ethics)

---

## Week 3 Deliverables Checklist
- [ ] P0.5 (CCR Framework) code complete + tested
- [ ] P0.6 (Audit Trail) code complete + tested
- [ ] Database migrations executed
- [ ] Frontend: CCR panel, audit dashboard, XAI viewer, research dashboard
- [ ] 20+ expert reviews collected
- [ ] H3 hypothesis validated (CCR ≥ 0.85 or documented)
- [ ] All tests passing (>80% coverage across backend + frontend)
- [ ] H1 + H2 + H3 validation reports finalized
- [ ] Compliance documentation complete
- [ ] **MERGE TO MAIN**: P0.5 + P0.6 code complete

---

---

# 🗓️ WEEK 4: INTEGRATION & PRODUCTION READINESS

## Frontend Tasks — Week 4

### UX Enhancement 4.1: Consent & Privacy UI (P0.9)
- [ ] **Component**: Create `ConsentFlow.tsx`
  - [ ] Step 1: Display full consent text (scrollable, required to read to end)
  - [ ] Step 2: Checkbox acceptance
  - [ ] Step 3: Signature (digital consent with timestamp)
  - [ ] Step 4: Confirmation + download PDF copy
  - [ ] PDF generation: Consent form stamped with date/time/anonymous ID
- [ ] **Sub-components**:
  - [ ] `ConsentText.tsx`: Scrollable consent document with scroll progress
  - [ ] `DigitalSignature.tsx`: E-signature capture
  - [ ] `ConsentPDF.tsx`: PDF generation + download
- [ ] **Testing**:
  - [ ] Test scroll-to-end requirement
  - [ ] Test signature capture
  - [ ] Test PDF generation + download
  - [ ] Test accessibility (WCAG 2.1 AA)

### UX Enhancement 4.2: User Feedback & Issue Reporting
- [ ] **Component**: Create `FeedbackWidget.tsx`
  - [ ] Floating button: "Send Feedback"
  - [ ] Modal form:
    - [ ] Category dropdown: Bug, Suggestion, Data issue
    - [ ] Screenshot capture (optional)
    - [ ] Text description
    - [ ] Contact email (optional)
  - [ ] Submit → send to backend + confirmation message
- [ ] **Testing**:
  - [ ] Test widget renders
  - [ ] Test form submission
  - [ ] Test screenshot capture

### UX Enhancement 4.3: Comprehensive Settings Page
- [ ] **Component**: Create `SettingsPage.tsx`
  - [ ] Section 1: Profile
    - [ ] Display user role (Clinician/MLEngineer/Admin)
    - [ ] Display organization
  - [ ] Section 2: Data & Privacy
    - [ ] Download my data (anonymized)
    - [ ] View audit trail (my predictions)
    - [ ] Revoke consents
  - [ ] Section 3: Preferences
    - [ ] Dashboard theme (light/dark)
    - [ ] Notification settings
    - [ ] Data export frequency
  - [ ] Section 4: Help & Support
    - [ ] FAQ link + search
    - [ ] Contact support
    - [ ] Documentation link
- [ ] **Testing**:
  - [ ] Test all sections render
  - [ ] Test data download functionality
  - [ ] Test consent revocation
  - [ ] Test preference save/load

### UX Enhancement 4.4: Mobile Responsive Optimization (All Pages)
- [ ] **Audit**: Review all Page components
  - [ ] [ ] Dashboard → mobile-friendly charts
  - [ ] [ ] AnalysisPage → stacked layout for results
  - [ ] [ ] ClinicalConcordancePanel → full-width Likert scales
  - [ ] [ ] AuditTrailDashboard → collapsible cards
  - [ ] [ ] Settings → single-column layout
- [ ] **Testing**:
  - [ ] Test all pages on 375px (mobile), 768px (tablet), 1920px (desktop)
  - [ ] Test touch interactions (buttons, scrolls, modals)
  - [ ] Test forms on mobile (input accessibility)
  - [ ] Performance test: Load time <3s on 4G

### UX Enhancement 4.5: Advanced Dashboard Analytics
- [ ] **Component**: Update `Dashboard.tsx` with new sections
  - [ ] Section 1: System Health (real-time from backend)
    - [ ] ML Service status (✓ Healthy / ⚠️ Degraded / ✗ Down)
    - [ ] Database status + query performance (avg query time)
    - [ ] Cache hit rate
    - [ ] API response time (avg, p95, p99)
  - [ ] Section 2: Model Performance
    - [ ] AUC scores (Fusion vs. Single-modality)
    - [ ] Inference time distribution (histogram)
    - [ ] Model version deployed + last update
  - [ ] Section 3: Usage Analytics (7-day rolling)
    - [ ] Predictions per hour (line chart)
    - [ ] Predictions by task (DR, glaucoma, refraction)
    - [ ] Unique patients analyzed
    - [ ] Expert reviews submitted (track h3 progress)
- [ ] **Testing**:
  - [ ] Test all charts load + display correctly
  - [ ] Test real-time updates (5s polling)
  - [ ] Test with 0 data points (graceful empty states)

---

## Backend Tasks — Week 4

### Backend 4.1: Secrets Management (P0.8)
- [ ] **Option A**: HashiCorp Vault (Production recommended)
  - [ ] Install Vault locally (dev mode for testing)
  - [ ] Create secret engine for Refracto secrets
  - [ ] Store secrets:
    - [ ] Database credentials
    - [ ] JWT secret
    - [ ] MinIO credentials
    - [ ] API keys (third-party services)
  - [ ] Create `.env` template (no values):
    ```
    VAULT_ADDR=http://vault:8200
    VAULT_TOKEN=<get from vault login>
    ```
  - [ ] Update main.py to load from Vault:
    ```python
    import hvac
    client = hvac.Client(url=os.getenv("VAULT_ADDR"))
    secrets = client.secrets.kv.list_secret_version_metadata(path='refracto')
    ```
- [ ] **Option B**: AWS Secrets Manager (Cloud alternative)
  - [ ] Create secret: `refracto-ai/production`
  - [ ] Store JSON with all credentials
  - [ ] Update app to fetch from AWS:
    ```python
    import boto3
    client = boto3.client('secretsmanager')
    secret = json.loads(client.get_secret_value(...)['SecretString'])
    ```
- [ ] **Verification**:
  - [ ] Remove all hardcoded secrets from docker-compose.yml
  - [ ] Remove all hardcoded secrets from config.py files
  - [ ] Scan codebase: `git log -p | grep -i 'password\|token\|secret'` → none
  - [ ] Test: App starts without .env file (loads from Vault)

### Backend 4.2: Docker Security Hardening
- [ ] **Modify** all Dockerfiles:
  - [ ] Use non-root user: `RUN useradd -m -u 1000 appuser && USER appuser`
  - [ ] Remove unnecessary packages: Minimal base images
  - [ ] Use multi-stage builds to reduce image size
  - [ ] Add health checks:
    ```dockerfile
    HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
      CMD curl -f http://localhost:8000/health || exit 1
    ```
  - [ ] Pin base image versions (no `latest` tags)
- [ ] **Security Scanning**:
  - [ ] Run Trivy: `trivy image <image-name>` → fix HIGH/CRITICAL vulnerabilities
  - [ ] Run docker scan: `docker scan` → verify no issues
- [ ] **Update** docker-compose.yml:
  - [ ] Use secrets instead of env vars:
    ```yaml
    secrets:
      db_password:
        file: /run/secrets/db_password
    services:
      postgres:
        environment:
          POSTGRES_PASSWORD_FILE: /run/secrets/db_password
    ```

### Backend 4.3: API Documentation & OpenAPI
- [ ] **Modify** `backend/services/ml_service/main.py`
  - [ ] Add FastAPI title, description, version:
    ```python
    app = FastAPI(
      title="Refracto AI - ML Service",
      description="Multi-Modal Learning for Ophthalmic Care",
      version="1.0.0"
    )
    ```
  - [ ] Add tags for endpoint organization:
    - [ ] `@app.post("/analyze/mtl", tags=["MTL Analysis"])`
    - [ ] `@app.post("/expert-review/add", tags=["Expert Review"])`
    - [ ] `@app.get("/audit/trail/{hash}", tags=["Audit Trail"])`
  - [ ] Generate OpenAPI schema: `curl http://localhost:8000/openapi.json`
  - [ ] Export to Swagger UI: Add `/docs` endpoint (auto-generated)
  - [ ] Export to ReDoc: Add `/redoc` endpoint (auto-generated)
- [ ] **Document** all endpoints:
  - [ ] Request + response schemas (Pydantic models)
  - [ ] Example requests + responses
  - [ ] Error codes + messages
- [ ] **Export** API documentation:
  - [ ] Save OpenAPI JSON: `openapi.json`
  - [ ] Generate API guide: `API_GUIDE.md`

### Backend 4.4: Monitoring & Logging
- [ ] **Add** Structured Logging to all services
  - [ ] Use `logging` + JSON formatter
  - [ ] Log format: `{"timestamp": "...", "level": "INFO", "service": "ml_service", "message": "...", "log_id": "..."}`
  - [ ] Add request ID tracking (propagate through all services)
  - [ ] Log all predictions with context
  - [ ] Log all errors with stack trace
- [ ] **Add** Health Check Endpoints
  - [ ] `GET /health` → returns `{"status": "healthy", "timestamp": "..."}`
  - [ ] `GET /metrics` → Prometheus metrics (optional, for advanced monitoring)
    - [ ] Prediction count
    - [ ] Inference time (p50, p95, p99)
    - [ ] Error rate
- [ ] **Integration**: Docker health checks
  - [ ] Modify docker-compose.yml to use `/health` endpoint

### Backend 4.5: Load Testing & Performance Optimization
- [ ] **Create** `backend/load_test.py`
  - [ ] Use `locust` library
  - [ ] Simulate 10 concurrent users
  - [ ] Each user: POST /analyze/mtl with random image
  - [ ] Run for 60 seconds
  - [ ] Check: Response time, error rate, throughput
  - [ ] Target: <200ms p95 response time, 0% errors
- [ ] **Performance Optimization**:
  - [ ] Add caching for model predictions (Redis)
  - [ ] Implement batch processing for multiple images
  - [ ] Profile slow endpoints using `cProfile`
  - [ ] Optimize database queries (add indexes, optimize joins)

### Backend 4.6: Kubernetes Manifests (K8s Deployment Ready)
- [ ] **Create** `kubernetes/` directory
  - [ ] `namespace.yaml`: Create `refracto` namespace
  - [ ] `postgres-deployment.yaml`: PostgreSQL statefulset
  - [ ] `auth-service-deployment.yaml`: Auth service
  - [ ] `ml-service-deployment.yaml`: ML service (2 replicas)
  - [ ] `imaging-service-deployment.yaml`: Imaging service
  - [ ] `patient-service-deployment.yaml`: Patient service
  - [ ] `services.yaml`: ClusterIP services for internal communication
  - [ ] `ingress.yaml`: Nginx ingress controller (expose /api/ml, /api/auth, etc.)
  - [ ] `configmap.yaml`: Non-secret configuration
  - [ ] `secrets.yaml`: External secrets (reference to Vault)
  - [ ] `hpa.yaml`: Horizontal Pod Autoscaler (scale based on CPU)
- [ ] **Deployment instructions**:
  - [ ] Create deployment guide: `KUBERNETES_DEPLOYMENT.md`
  - [ ] Test locally with `minikube` or `kind`

---

## Testing Tasks — Week 4

### End-to-End (E2E) Testing: Full System Flow
- [ ] **Create** `backend/tests/test_e2e_full_system.py`
  - [ ] Scenario 1: Patient Registration → Image Upload → MTL Analysis → Expert Review → CCR Calculation
    - [ ] Register local patient → anonymized ID
    - [ ] Upload Fundus + OCT images → verify ingestion
    - [ ] Run MTL analysis → verify predictions
    - [ ] Submit expert review → verify CCR updated
    - [ ] Query audit trail → verify log entry
    - [ ] All database tables updated ✓
  - [ ] Scenario 2: Secrets Management → Service Startup
    - [ ] Store secrets in Vault
    - [ ] Start services (no .env file)
    - [ ] Services connect to DB successfully
    - [ ] API endpoints respond correctly
  - [ ] Run: `pytest tests/test_e2e_full_system.py -v`

### Security Testing
- [ ] **Create** `backend/tests/test_security.py`
  - [ ] Test: No hardcoded secrets in code/config
  - [ ] Test: No PII in API responses
  - [ ] Test: Authentication required for protected endpoints
  - [ ] Test: Authorization (clinician can't access admin endpoints)
  - [ ] Test: Input validation (SQL injection, XSS, path traversal)
  - [ ] Test: Rate limiting (if implemented)
  - [ ] Run: `pytest tests/test_security.py -v`

### Performance & Load Testing
- [ ] **Run** `backend/load_test.py`
  - [ ] 10 concurrent users
  - [ ] 100 requests total
  - [ ] Report: Response times, error rate, throughput
  - [ ] Target: p95 < 300ms, error rate 0%
  - [ ] Document results in `PERFORMANCE_REPORT_W4.md`

### Accessibility Testing (Frontend)
- [ ] **Run** `npm run a11y-audit`
  - [ ] Check all pages for WCAG 2.1 AA compliance
  - [ ] Run Lighthouse audit on each page
  - [ ] Fix critical issues (color contrast, heading hierarchy, alt text)
  - [ ] Document results: `ACCESSIBILITY_REPORT_W4.md`

### Browser Compatibility Testing (Frontend)
- [ ] **Test** on multiple browsers (BrowserStack or local)
  - [ ] Chrome (latest 2 versions)
  - [ ] Firefox (latest 2 versions)
  - [ ] Safari (latest 2 versions)
  - [ ] Edge (latest 2 versions)
  - [ ] Mobile browsers (iOS Safari, Chrome Mobile)
  - [ ] Report: any issues + fixes

### Regression Testing
- [ ] **Suite** of 50+ tests covering all Week 1-3 features
  - [ ] Run full test suite: `npm test && pytest tests/ -v`
  - [ ] Target: 100% pass rate
  - [ ] Coverage: >80% for all critical features
  - [ ] Report: `REGRESSION_TEST_REPORT_W4.md`

---

## Documentation Tasks — Week 4

### Users & Stakeholders Documentation
- [ ] **Create** `CLINICIAN_GUIDE.md`
  - [ ] How to upload images
  - [ ] How to review MTL predictions
  - [ ] How to submit expert reviews (CCR)
  - [ ] FAQ: "What is CCR?" / "Why is myopia correction applied?" / etc.
  - [ ] Troubleshooting: Common issues + solutions
  - [ ] Screenshots: UI walkthrough

- [ ] **Create** `ADMIN_GUIDE.md`
  - [ ] System setup + requirements
  - [ ] User management (create/delete/roles)
  - [ ] Data management (backup, export, cleanup)
  - [ ] Monitoring dashboard
  - [ ] Troubleshooting: Common deployment issues

- [ ] **Create** `PATIENT_DATA_GUIDE.md`
  - [ ] Consent process (patient-facing)
  - [ ] Data privacy & anonymization
  - [ ] How to access/download personal data
  - [ ] How to revoke consent

### Developer Documentation
- [ ] **Create/Update** `CONTRIBUTING.md`
  - [ ] How to set up dev environment
  - [ ] Code style guidelines (PEP 8, ESLint)
  - [ ] Git workflow (branches, PRs, commit message format)
  - [ ] Testing requirements (unit + integration + E2E)
  - [ ] Deployment process

- [ ] **Create** `DEVELOPER_API.md`
  - [ ] Architecture overview
  - [ ] Service-to-service communication
  - [ ] Database schema + relationships
  - [ ] How to add new endpoints + models
  - [ ] How to extend ML models

### Research Documentation
- [ ] **Create** `RESEARCH_METHODOLOGY.md`
  - [ ] Overview of all 3 hypotheses
  - [ ] Data collection protocol
  - [ ] Validation procedures
  - [ ] Statistical methods (AUC, CCR calculation, FPR)
  - [ ] Ethics approval documentation

- [ ] **Create** `RESULTS_SUMMARY.md` (Week 4 Final Results)
  - [ ] H1 Fusion Superiority: Results table, statistical significance
  - [ ] H2 Refracto-Link: FPR reduction %, high-myopia cohort performance
  - [ ] H3 Clinical Concordance: CCR %, expert breakdown, task breakdown
  - [ ] Overall: Objectives met? (O1-O5 completion status)

### System Documentation
- [ ] **Create** `ARCHITECTURE.md` (Comprehensive)
  - [ ] Microservices architecture diagram
  - [ ] Data flow diagram (end-to-end)
  - [ ] Technology stack + versions
  - [ ] Deployment architecture (Docker Compose vs. K8s)

- [ ] **Create** `DEPLOYMENT_GUIDE.md`
  - [ ] Prerequisites (Docker, PostgreSQL, etc.)
  - [ ] Option 1: Local Development Setup
  - [ ] Option 2: Docker Compose Deployment
  - [ ] Option 3: Kubernetes Deployment
  - [ ] Post-deployment verification checklist

- [ ] **Update** `README.md` (Root)
  - [ ] Project overview + research objectives
  - [ ] Quick start (3 steps to run)
  - [ ] Links to detailed docs
  - [ ] Repository structure brief
  - [ ] Contributing guidelines link

---

## Research Validation — Week 4 (FINAL)

### Complete Research Objective Validation

| Objective | P0 Features | Status | Evidence | W4 Checkpoint |
|-----------|-----------|--------|----------|-----------|
| O1: Hybrid MTL | P0.1, P0.2 | ✓ Complete | Fusion code + tests | MTL model live |
| O2: Validation Pipeline | P0.3, P0.4, P0.5 | ✓ Complete | 50 patients, CCR framework | CCR ≥85% or doc actual |
| O3: Refracto-Path Link | P0.2 | ✓ Complete | Correction logic + tests | FPR reduction ≥20% or doc |
| O4: XAI + Clinical Trust | P0.6 | ✓ Complete | Audit trail operational | All predictions logged |
| O5: Local Generalization | P0.4 | ✓ Complete | Local data manager | 50 local patients enrolled |

### Final Research Reports

- [ ] **Create** `HYPOTHESIS_VALIDATION_FINAL.md`
  - [ ] H1: Fusion AUC improvement ≥3% → PASS/FAIL
  - [ ] H2: FPR reduction ≥20% (myopia) → PASS/FAIL
  - [ ] H3: CCR ≥85% → PASS/FAIL
  - [ ] Statistical significance testing (if applicable)
  - [ ] Confidence intervals
  - [ ] Conclusion + future work

- [ ] **Create** `ETHICS_COMPLIANCE_SUMMARY.md`
  - [ ] Ethics approval obtained: YES/NO + reference ID
  - [ ] Anonymization verified: YES/NO + spot-check samples
  - [ ] Consent tracking: n=50 patients with valid consent
  - [ ] Audit trail implemented: YES + sample entries
  - [ ] Data access controls: Implemented + tested
  - [ ] GDPR compliance: Assessed + documented

- [ ] **Create** `PHASE1_COMPLETION_REPORT.md` (Executive Summary)
  - [ ] All 9 P0 features: Status (✓ Complete)
  - [ ] Testing: Coverage %, pass rate %, known issues
  - [ ] Research validation: H1/H2/H3 status
  - [ ] Next steps: Transition to Phase 2
  - [ ] Lessons learned + recommendations

---

## Week 4 Integration Checklist

### Final Code Review (All PRs)
- [ ] All P0.1-P0.9 code reviewed + approved
- [ ] All conflicts merged
- [ ] All tests passing (100% for critical features)
- [ ] Documentation complete
- [ ] No hardcoded secrets
- [ ] No breaking changes

### Deployment to Staging
- [ ] Build Docker images for all services
- [ ] Push to Docker registry (Docker Hub or private)
- [ ] Deploy to staging environment (docker-compose or K8s)
- [ ] Run smoke tests: All endpoints respond
- [ ] Run E2E tests on staging
- [ ] Performance testing: <300ms p95 latency
- [ ] Security scan: Trivy + docker scan

### Stakeholder Sign-Off
- [ ] Demo system to ethics committee
-  [ ] Demo system to clinical advisors
- [ ] Demo system to research advisor
- [ ] Collect feedback + document
- [ ] Incorporate feedback (if time allows)

### Production Readiness Checklist
- [ ] [ ] Monitoring configured (logging, metrics, health checks)
- [ ] [ ] Backup strategy documented + tested
- [ ] [ ] Disaster recovery plan documented
- [ ] [ ] Runbooks created for common issues
- [ ] [ ] On-call procedures defined
- [ ] [ ] Uptime target defined (99% uptime? 99.9%?)
- [ ] [ ] SLA documented

---

## Week 4 Final Deliverables

### Code
- [ ] All 9 P0 features code-complete
- [ ] All services deployed + tested
- [ ] Kubernetes manifests ready (optional, for production scaling)
- [ ] Docker images secured + scanned

### Testing
- [ ] 200+ total tests (unit + integration + E2E)
- [ ] >80% code coverage
- [ ] 0 known critical bugs
- [ ] Performance validated (<300ms p95)
- [ ] Security tested (no vulnerabilities)
- [ ] Accessibility compliant (WCAG 2.1 AA)

### Documentation
- [ ] Clinician user guide
- [ ] Admin deployment guide
- [ ] Developer API documentation
- [ ] Research methodology documented
- [ ] Final hypothesis validation reports
- [ ] Phase 1 completion summary

### Research
- [ ] All 3 hypotheses validated (status documented)
- [ ] All 5 research objectives completed
- [ ] Ethics approval + compliance verified
- [ ] Local data collection complete (50 patients)
- [ ] Expert panel validated system (CCR ≥85% or actual value)

### Deployment
- [ ] Staging deployment successful
- [ ] All stakeholder sign-offs obtained
- [ ] Production readiness achieved

---

# 📊 MASTER CHECKLIST: ALL TASKS SUMMARY

## Week 1: Foundation (28 tasks)
- [ ] Frontend: Multi-Modal Uploader (5)
- [ ] Frontend: MTL Results Panel (5)
- [ ] Backend: Fusion module (5)
- [ ] Backend: Refracto-Link (5)
- [ ] Tests: Fusion + Link + E2E (8)

## Week 2: Data (35 tasks)
- [ ] Frontend: Image Gallery (5)
- [ ] Frontend: Patient Wizard (8)
- [ ] Frontend: Quality Indicators (5)
- [ ] Backend: Ingestion pipeline (8)
- [ ] Backend: Local Data Manager (8)
- [ ] Tests: Ingestion + Local Data (5)
- [ ] Research: Local data collection (5)

## Week 3: Validation (42 tasks)
- [ ] Frontend: CCR Panel (8)
- [ ] Frontend: Audit Dashboard (8)
- [ ] Frontend: XAI Viewer (8)
- [ ] Frontend: Research Dashboard (5)
- [ ] Backend: CCR framework (8)
- [ ] Backend: Audit Trail (8)
- [ ] Tests: CCR + Audit tests (5)
- [ ] Research: H1/H2/H3 validation (5)

## Week 4: Production (48 tasks)
- [ ] Frontend: Consent UI (8)
- [ ] Frontend: Settings (8)
- [ ] Frontend: Mobile optimization (8)
- [ ] Frontend: Advanced analytics (8)
- [ ] Backend: Secrets management (5)
- [ ] Backend: Security hardening (5)
- [ ] Backend: API documentation (5)
- [ ] Backend: K8s manifests (5)
- [ ] Tests: E2E + Security + Performance (10)
- [ ] Documentation: 7 guides (7)

---

## TOTAL EFFORT ESTIMATE

| Category | Tasks | Hours | Owner |
|----------|-------|-------|-------|
| **Frontend Development** | 50+ | 120 hrs | Frontend Engineer |
| **Backend Development** | 40+ | 130 hrs | Backend + ML Engineer |
| **Testing** | 60+ | 80 hrs | QA Engineer |
| **Documentation** | 20+ | 30 hrs | Tech Writer + All |
| **Research Validation** | 15+ | 40 hrs | ML Engineer + Clinicians |

**Total**: 153+ tasks | 400+ hours | 4 weeks | 2-4 person team

---

## Success Criteria (Week 4 Gate)

Before moving to Phase 2, verify:

✅ **Technical**
- [ ] All 9 P0 features code-complete
- [ ] 100% of critical tests passing
- [ ] Code reviewed + merged to main
- [ ] Production deployment successful

✅ **Research**
- [ ] H1: Fusion superiority validated (any positive result)
- [ ] H2: Refracto-link effectiveness validated (FPR drop quantified)
- [ ] H3: Clinical Concordance ≥85% achieved
- [ ] All 5 research objectives 100% complete

✅ **Compliance**
- [ ] Ethics approval documented
- [ ] 50+ local patients registered (anonymized)
- [ ] Audit trail operational + verified
- [ ] Zero PII in any system output

✅ **User Experience**
- [ ] All frontend components responsive + tested
- [ ] Clinician workflow smooth (5 clicks to analysis + review)
- [ ] Mobile usable (tested on iOS + Android)
- [ ] Accessibility compliant (WCAG 2.1 AA)

---

**Ready to execute? Start with Week 1, Day 1: Create frontend components + backend fusion module!** 🚀

