# Gap Analysis: Research Proposal vs Current Implementation
**Refracto AI - A Hybrid XAI Clinical Decision Support System for Integrated Ophthalmic Care**

---

## Executive Summary

The current implementation provides a solid **microservices foundation** and **basic ML inference pipeline**, but is missing **22 critical features** required by the research proposal. The system needs architectural enhancements to support:
1. **Multi-Task Learning (MTL)** fusion architecture
2. **Refracto-Pathological relationship modeling**
3. **Multi-modal data fusion** (Fundus + OCT + Structured)
4. **Comprehensive XAI** (Grad-CAM + SHAP)
5. **Clinical validation framework**
6. **Local data management and fine-tuning**

---

## Part A: MISSING FEATURES (Not Implemented)

### A1. Core ML Architecture (4 features)

| Feature | Current State | Required State | Impact | Priority |
|---------|---------------|----------------|--------|----------|
| **Multi-Task Learning (MTL) Unified Architecture** | Separate inference heads for refraction and pathology | Single encoder with dual task heads sharing features | **CRITICAL** — Proposal mandates MTL for mutual learning; current design siloes tasks | P0 |
| **Multi-Modal Fusion Layer** | ViT and EfficientNet loaded separately; no fusion | Centralized fusion of fundus + OCT features before classification | **CRITICAL** — H1 hypothesis depends on multi-modal fusion superiority | P0 |
| **Structured Data Integration (Gradient Boosting Module)** | Not implemented | Age, IOP, Diabetes Status, Spherical Equivalent inputs to GBM layer | **HIGH** — Proposal specifies structured data fusion for clinical realism | P1 |
| **Refracto-Pathological Link Module** | Not implemented | Explicit feature linking refractive status (myopia) to glaucoma false-positive reduction | **CRITICAL** — H2 hypothesis core; Section 3 conceptual framework | P0 |

---

### A2. Explainability & Interpretability (3 features)

| Feature | Current State | Required State | Impact | Priority |
|---------|---------------|----------------|--------|----------|
| **SHAP Integration** | Not implemented | SHAP values for structured data (Age, IOP, DM) contribution to diagnosis | **HIGH** — Proposal requires both Grad-CAM and SHAP (Section 3, 12.5) | P1 |
| **Natural Language Report Generation** | Not implemented | Auto-generated clinical reports linking XAI findings to clinical context | **HIGH** — Section 4, Objective 4: "educational, natural language reports" | P1 |
| **XAI Dashboard/Visualization Hub** | Not implemented | Centralized UI showing Grad-CAM, SHAP, confidence scores, clinical reasoning | **MEDIUM** — Supports clinician trust and adoption | P2 |

---

### A3. Data Infrastructure & Management (5 features)

| Feature | Current State | Required State | Impact | Priority |
|---------|---------------|----------------|--------|----------|
| **Multi-Modal Data Ingestion Pipeline** | Single image uploads only | Co-registered Fundus + OCT + DICOM ingestion; automated pairing | **CRITICAL** — Sample size target >15,000 co-registered pairs (Section 9) | P0 |
| **Label Harmonization & Standardization Engine** | Basic CSV loading | Unified label schema for DR grades (0–4), Glaucoma (binary/severity), Refractive (sphere/cylinder/axis) | **HIGH** — Section 11 mandates harmonization | P1 |
| **Sri Lankan Local Patient Data Management** | Not implemented | Secure, anonymized local data collection module with consent/audit logging | **CRITICAL** — Objective 5 requires local validation (N=300–500 patients) | P0 |
| **Data Curation & Quality Checks** | Not implemented | Image quality, label consistency, co-registration validation workflows | **HIGH** — Data quality directly impacts model performance | P1 |
| **Cohort Stratification & Filtering** | Not implemented | Dynamic patient cohort management (filter by: Myopia, DR Grade, Glaucoma Risk, Age, DM Status) | **MEDIUM** — Objective 2 (validation on specific subgroups) | P2 |

---

### A4. Clinical Validation & Evaluation (4 features)

| Feature | Current State | Required State | Impact | Priority |
|---------|---------------|----------------|--------|----------|
| **Clinical Concordance Rate (CCR) Measurement System** | Not implemented | Panel-based expert review interface; CCR > 85% scoring (H3 validation) | **CRITICAL** — H3 hypothesis directly (Section 5); Section 12.5 focus | P0 |
| **Comprehensive Evaluation Metrics Framework** | Basic accuracy only | AUC, Sensitivity, Specificity, Balanced Accuracy, MAE, F1, Confusion Matrices per disease | **HIGH** — Research methodology (Section 6, 11) requires multi-metric validation | P1 |
| **Holdout Test Set Management** | Single split only | 70/15/15 split with stratification by disease/cohort; cross-validation options | **MEDIUM** — Rigorous ML best practices (Section 11) | P1 |
| **Performance Regression Detection** | Not implemented | Automated alerts when model performance drops on new data (clinical safeguard) | **MEDIUM** — Ensures reliability for clinical deployment | P2 |

---

### A5. Model Training & Fine-Tuning (2 features)

| Feature | Current State | Required State | Impact | Priority |
|---------|---------------|----------------|--------|----------|
| **Multi-Stage Training Pipeline** | Single training script | Phase 1 (foreign data): train encoders; Phase 2 (local data): fine-tune with task freezing/unfreezing | **HIGH** — Research design mandates two-phase approach (Phases P2–P3, Section 14) | P1 |
| **Curriculum Learning & Class Balancing** | Basic implementation | Weighted sampling, progressive learning (easy→hard samples), SMOTE for imbalanced pathologies | **MEDIUM** — Improves generalization and convergence | P2 |

---

### A6. Clinical Integration & Audit (3 features)

| Feature | Current State | Required State | Impact | Priority |
|---------|---------------|----------------|--------|----------|
| **Ethical Audit Trail & Decision Logging** | Not implemented | Immutable log of each diagnosis (timestamp, patient ID hash, prediction, confidence, clinician action) | **CRITICAL** — No-Harm Principle (Section 10); regulatory compliance | P0 |
| **Bias & Fairness Monitoring** | Not implemented | Dashboard tracking model performance across ethnicity, age, DM status (detect algorithmic bias) | **HIGH** — Section 10 mandates generalizability bias mitigation | P1 |
| **Clinician Feedback Loop** | Not implemented | Button for clinicians to flagIncorrect predictions; data collected for model retraining | **MEDIUM** — Continuous improvement mechanism | P2 |

---

### A7. DevOps & Infrastructure (1 feature)

| Feature | Current State | Required State | Impact | Priority |
|---------|---------------|----------------|--------|----------|
| **Model Registry & Versioning** | Models stored as `.pth` files | Centralized model registry with metadata (training date, performance metrics, acceptable use conditions) | **MEDIUM** — Production readiness; experiment tracking (MLflow or similar) | P1 |

---

## Part B: FEATURES TO ENHANCE (Existing but Incomplete/Suboptimal)

### B1. Architecture & Design (4 features)

| Feature | Current State | Enhancement Need | Impact | Priority |
|-----|-----|-----|-----|-----| 
| **ML Service Modularity** | Monolithic main.py with copypasta endpoints | Refactor into composable modules: `tasks.py`, `fusion.py`, `evaluation.py`, `xai.py` | **MEDIUM** — Code maintainability; easier testing | P2 |
| **Frontend-Backend API Contract** | Loose coupling; hardcoded URLs | Formal OpenAPI schema; versioned API; deprecation warnings | **MEDIUM** — Stability; easier scaling | P2 |
| **Error Handling & Logging** | Basic logging | Structured logging (JSON); error classification (user vs system); graceful fallbacks | **HIGH** — Production readiness; debugging | P1 |
| **Dependency Management** | Pinned versions in requirements.txt | Add version ranges; separate dev/prod requirements; security scanning (pip-audit) | **HIGH** — Security; reproducibility | P1 |

---

### B2. Database & Data Models (3 features)

| Feature | Current State | Enhancement Need | Impact | Priority |
|-----|-----|-----|-----|-----| 
| **Patient Data Schema** | Minimal fields (UUID, name, DOB, gender, DM status) | Extend: IOP, Axial Length, Cup-to-Disc Ratio, Spherical Equivalent, Previous diagnoses, Consent audit | **HIGH** — Richer clinical context | P1 |
| **Imaging Metadata Model** | Basic (patient_id, type, size, upload_at) | Add: image_quality_score, modality_subtype (ODense OCT variant), equipment_id, co_registration_status, processed_at | **HIGH** — Traceability; quality controls | P1 |
| **Diagnosis & Prediction Audit Table** | Not fully modeled | `PredictionLog` table: patient_id, model_version, input_metadata, predictions, confidence, clinician_override, feedback_flag, created_at | **CRITICAL** — Audit trail; ethics compliance | P0 |

---

### B3. ML Model Enhancement (4 features)

| Feature | Current State | Enhancement Need | Impact | Priority |
|-----|-----|-----|-----|-----| 
| **Attention Mechanism in Fusion** | Simple concatenation | Multi-head cross-attention between modality branches (Transformer-style attention) | **MEDIUM** — Improves feature interaction modeling | P2 |
| **Uncertainty Quantification** | Confidence scores only | Bayesian uncertainty (MC-Dropout, ensemble); out-of-distribution detection | **HIGH** — Clinical safety; risk stratification | P1 |
| **Grad-CAM Target Layer Flexibility** | Hardcoded for EfficientNet | Automatic multi-layer CAM generation; comparison of different target layers | **LOW** — Interpretability depth | P3 |
| **DICOM Support in Preprocessing** | JPG/PNG only | Full DICOM parsing; window/level adjustments; multi-frame sequences | **MEDIUM** — Real-world hospital integration | P2 |

---

### B4. Validation & Testing (4 features)

| Feature | Current State | Enhancement Need | Impact | Priority |
|-----|-----|-----|-----|-----| 
| **Unit Tests** | Minimal/absent | Test models: refraction head, fusion layer, XAI pipeline; test API endpoints | **HIGH** — CI/CD readiness; regression prevention | P1 |
| **Integration Tests** | Not formalized | End-to-end workflows: upload→preprocess→predict→xai_report | **MEDIUM** — System stability | P1 |
| **Validation on External Datasets** | RFMiD/GAMMA mentioned, not used | Auto-download and periodic benchmark on RFMiD test splits | **HIGH** — Objective 2 (foreign data validation) | P1 |
| **Performance Dashboards** | Raw metrics in logs | Real-time Grafana/Plotly dashboards: model accuracy, inference latency, GPU usage, error rates | **MEDIUM** — Operational visibility | P2 |

---

### B5. Frontend Enhancements (4 features)

| Feature | Current State | Enhancement Need | Impact | Priority |
|-----|-----|-----|-----|-----| 
| **Dynamic Result Rendering** | Static mock results | Real AnalysisResult binding: refraction values, DR/Glaucoma scores from API | **HIGH** — End-to-end functionality | P1 |
| **Multi-Modal Image Viewer** | Single fundus viewer | Side-by-side Fundus + OCT viewer; alignment/overlay tools; zoom/pan controls | **HIGH** — Clinical usability | P1 |
| **Admin/Analytics Panel** | Not implemented | Dashboard: patient cohort stats, model performance, pending analyses, feedback queue | **MEDIUM** — Operational management | P2 |
| **Consent & Privacy UI** | Not implemented | GDPR/local compliance: informed consent flow, anonymization confirmation, audit log viewer | **CRITICAL** — Ethical compliance (Section 10) | P0 |

---

### B6. DevOps & Deployment (3 features)

| Feature | Current State | Enhancement Need | Impact | Priority |
|-----|-----|-----|-----|-----| 
| **Container Security** | Standard Dockerfile | Multi-stage builds; non-root user; vulnerability scanning (Trivy) | **MEDIUM** — Security posture | P2 |
| **Secrets Management** | `.env` file (risky) | HashiCorp Vault / AWS Secrets Manager; no hardcoded credentials in docker-compose | **CRITICAL** — Security | P0 |
| **Kubernetes Manifests** | docker-compose only | k8s YAML for scaling ML service; auto-restart policies; resource limits | **MEDIUM** — Production deployment | P2 |

---

### B7. Documentation & Governance (3 features)

| Feature | Current State | Enhancement Need | Impact | Priority |
|-----|-----|-----|-----|-----| 
| **API Documentation** | Auto-generated `/docs` | Detailed endpoint descriptions; example payloads; error codes | **MEDIUM** — Developer onboarding | P2 |
| **Model Card & Governance** | Not formalized | Model Card (performance on subgroups, limitations, use cases, ethical considerations) | **HIGH** — Transparency; responsible AI | P1 |
| **Runbook & Troubleshooting** | Basic README | Detailed deployment, local dev setup, debugging model behavior, common errors | **MEDIUM** — Operations | P2 |

---

## Summary Table: Total Count

| Category | Missing | To Enhance | Total |
|----------|---------|------------|-------|
| **A1: ML Architecture** | 4 | — | 4 |
| **A2: XAI** | 3 | — | 3 |
| **A3: Data Infrastructure** | 5 | — | 5 |
| **A4: Clinical Validation** | 4 | — | 4 |
| **A5: Training** | 2 | — | 2 |
| **A6: Audit & Clinical** | 3 | — | 3 |
| **A7: DevOps** | 1 | — | 1 |
| **B1: Architecture** | — | 4 | 4 |
| **B2: Data Models** | — | 3 | 3 |
| **B3: ML Enhancement** | — | 4 | 4 |
| **B4: Validation** | — | 4 | 4 |
| **B5: Frontend** | — | 4 | 4 |
| **B6: DevOps** | — | 3 | 3 |
| **B7: Documentation** | — | 3 | 3 |
| **TOTAL** | **22** | **26** | **48** |

---

## Implementation Priority Roadmap

### Phase 1 (Weeks 1–4): Critical Foundations — P0 Features
1. **Multi-Modal Fusion Architecture** (A1.2)
2. **Refracto-Pathological Link Module** (A1.4)
3. **Multi-Modal Data Ingestion** (A3.1)
4. **Sri Lankan Data Management** (A3.3)
5. **Clinical Concordance CCR Framework** (A4.1)
6. **Ethical Audit Trail** (A6.1)
7. **Prediction Log DB Schema** (B2.3)
8. **Secrets Management** (B6.2)
9. **Consent & Privacy UI** (B5.4)

### Phase 2 (Weeks 5–8): Core Features — P1 Features
1. **Structured Data Integration (GBM)** (A1.3)
2. **Label Harmonization Engine** (A3.2)
3. **SHAP Integration** (A2.1)
4. **Natural Language Report Generation** (A2.2)
5. **Multi-Stage Training Pipeline** (A5.1)
6. **Evaluation Metrics Framework** (A4.2)
7. **Data Quality & Curation** (A3.4)
8. **Uncertainty Quantification** (B3.2)
9. **Unit & Integration Tests** (B4.1, B4.2)
10. **Dynamic Frontend Result Binding** (B5.1)
11. **Multi-Modal Image Viewer** (B5.2)
12. **Error Handling & Logging** (B1.3)
13. **Dependency Management** (B1.4)
14. **Patient Data Schema Extension** (B2.1)
15. **Imaging Metadata Extension** (B2.2)
16. **Model Card & Governance** (B7.2)

### Phase 3 (Weeks 9–12): Enhancement & Polish — P2 Features
1. **XAI Dashboard** (A2.3)
2. **Bias & Fairness Monitoring** (A6.2)
3. **Clinician Feedback Loop** (A6.3)
4. **Cohort Stratification** (A3.4)
5. **Model Registry & Versioning** (A7.1)
6. **ML Service Modularity** (B1.1)
7. **API Contract Versioning** (B1.2)
8. **Attention Mechanism** (B3.1)
9. **DICOM Support** (B3.4)
10. **External Dataset Benchmarking** (B4.3)
11. **Performance Dashboards** (B4.4)
12. **Admin/Analytics Panel** (B5.3)
13. **Container Security** (B6.1)
14. **Kubernetes Manifests** (B6.3)
15. **API Documentation Enhancement** (B7.1)
16. **Runbook & Troubleshooting** (B7.3)

---

## Alignment with Research Proposal

### Objectives Mapping

| Research Objective | Required Features | Current Coverage |
|-------------------|-------------------|------------------|
| **Obj 1**: Hybrid MTL Architecture Design | A1.1, A1.2 | 20% (basic arch exists) |
| **Obj 2**: Integrated Prediction Validation | A4.2, B4.1–B4.3 | 40% (basic metrics) |
| **Obj 3**: Establish Refracto-Pathological Link | A1.4, A3.1 | 5% (concept only) |
| **Obj 4**: XAI Integration and Clinical Trust | A2.1–A2.3, A6.1 | 25% (Grad-CAM partial) |
| **Obj 5**: Local Generalization & Utility | A3.3, A4.1, A5.1 | 10% (setup only) |

### Hypotheses Mapping

| Hypothesis | Supporting Features | Status |
|-----------|-------------------|--------|
| **H1**: Multi-Modal Fusion Superiority | A1.2, B4.3, B3.1 | Not testable (fusion missing) |
| **H2**: Refracto-Pathological Link Reduces FPR | A1.4, A6.2 | Not testable (link missing) |
| **H3**: CCR > 85% Achievement | A4.1, A2.2 | Not measurable (framework missing) |

---

## Key Risks & Mitigation

| Risk | Current State | Mitigation (Implementation) |
|------|---------------|---------------------------|
| **Siloed Task Learning** | Model maintains separate heads | Implement MTL encoder sharing (A1.1) |
| **Multimodal Data Scarcity** | Only single-modality uploads supported | Build co-registration pipeline (A3.1) |
| **Black-Box Model** | Only Grad-CAM; no multimodal explanation | Add SHAP + natural language reports (A2.1–A2.3) |
| **Ethical/Privacy Gaps** | No audit trail or consent flow | Implement audit logging + privacy UI (A6.1, B5.4) |
| **Local Data Absence** | No Sri Lankan patient collection | Build local data management module (A3.3) |
| **Clinician Distrust** | No clinical validation metrics | Establish CCR measurement framework (A4.1) |

---

## Next Steps

1. **Prioritize Phase 1 features** for immediate architecture overhaul
2. **Create feature branches** for each module (fusion, MTL, audit, etc.)
3. **Begin with MTL refactor** and multi-modal fusion layer (highest impact)
4. **Parallel track**: Database schema migration for audit trail + local data
5. **Communication**: Update research timeline and stakeholders on implementation status

---

**Document Generated**: March 12, 2026  
**Project Name**: Refracto AI - Hybrid XAI Clinical Decision Support System  
**Research Proposal Student**: K.M.P. Jayalath (IT_IFLS_001/B003/0020)

