# Refracto AI: Quick Implementation Roadmap
**Status**: Gap Analysis Complete | Ready for Phase 1 Development  
**Date**: March 12, 2026  
**Student**: K.M.P. Jayalath (IT_IFLS_001/B003/0020)

---

## Current vs. Target Architecture

### Current (As-Is)
```
Microservices ✓ │ Basic ML Engine ✓ │ API Endpoints ✓ │ React Frontend ✓
     ↓              ↓                    ↓                    ↓
[Auth] [Img] [ML] [Pat] [DICOM]    Single Models       /analyze /predict    Dashboard only
     Database: Minimal schema        Separate heads      Hardcoded responses
```

**Gaps**: Multi-modal fusion × Refracto-pathology link × XAI (SHAP) × Clinical validation × Local data × Audit trail

### Target (To-Be)
```
Unified MTL ─→ Multi-Modal Fusion ──→ Refracto-Link ──→ Dual XAI (Grad-CAM+SHAP)
    ↓                    ↓                  ↓                     ↓
[Ethics Audit] ← Prediction Log ← Clinical CCR ← Expert Review Panel
    ↓
[Local Data Manager] ← Anonymization ← Consent Mgmt
    ↓
[Dashboard] ← Performance Metrics ← Bias Monitoring
```

---

## The 48 Features: At-a-Glance Breakdown

### **✗ MISSING (22 features requiring new development)**

**Critical Path (Week 1–4): 9 Features**
1. **Multi-Task Learning (MTL) Architecture** — Shared encoder → dual task heads
2. **Multi-Modal Fusion Layer** — Fundus + OCT feature fusion
3. **Refracto-Pathological Link** — Myopia ↔ Glaucoma artifact correction
4. **Multi-Modal Data Ingestion** — Co-registered Fundus/OCT pairing
5. **Local Data Management** — Sri Lankan patient data + anonymization
6. **Clinical Concordance Framework** — Expert panel CCR measurement
7. **Ethical Audit Trail** — Immutable prediction logs
8. **Secrets Management** — Replace hardcoded credentials
9. **Consent & Privacy UI** — GDPR/local compliance flow

**Secondary Features (Week 5–8): 8 Features**
10. Structured Data Integration (Gradient Boosting Module)
11. Label Harmonization Engine
12. SHAP Integration (post-hoc explainability)
13. Natural Language Report Generation
14. Multi-Stage Training Pipeline
15. Comprehensive Evaluation Metrics
16. Uncertainty Quantification
17. Clinician Feedback Loop

**Enhancement Features (Week 9–12): 5 Features**
18. XAI Dashboard
19. Bias & Fairness Monitoring
20. Data Quality & Curation
21. Cohort Stratification
22. Model Registry & Versioning

### **↗ NEEDS ENHANCEMENT (26 features requiring refactoring)**

**Immediate**: Error handling, dependency management, secrets rotation
**Data Models**: Patient schema, imaging metadata, prediction auditing
**Testing**: Unit/integration tests, external validation, performance dashboards
**DevOps**: Container security, Kubernetes templates, runbooks

---

## Implementation Phases

```
Phase 1 (Weeks 1–4): CRITICAL FOUNDATIONS
├─ P0.1: Multi-Modal Fusion Architecture
├─ P0.2: Refracto-Pathological Link Module
├─ P0.3: Multi-Modal Data Ingestion Pipeline
├─ P0.4: Sri Lankan Local Data Manager
├─ P0.5: Clinical Concordance (CCR) Framework
├─ P0.6: Ethical Audit Trail & Logging
├─ P0.7: Database Schema Migration
├─ P0.8: Secrets Management (Vault)
└─ P0.9: Consent & Privacy UI

Phase 2 (Weeks 5–8): CORE FEATURES  
├─ P1.1: Structured Data Integration (GBM)
├─ P1.2: Label Harmonization Engine
├─ P1.3: SHAP Integration
├─ P1.4: Natural Language Reports
├─ P1.5: Multi-Stage Training Pipeline
├─ P1.6: Comprehensive Metrics Framework
├─ P1.7: Uncertainty Quantification
├─ P1.8: Clinician Feedback Loop
└─ [+8 Testing/Frontend/DevOps features]

Phase 3 (Weeks 9–12): POLISH & SCALE
├─ P2.1: XAI Dashboard
├─ P2.2: Bias Monitoring System
├─ P2.3: Performance Dashboards
├─ P2.4: Kubernetes Manifests
└─ [Documentation, security hardening, optimization]
```

---

## Key Alignment with Research Proposal

| Proposal Objective | Critical Features | Status | Delivery |
|-------------------|-------------------|--------|----------|
| **Objective 1**: Design Hybrid MTL | P0.1, P0.2 | 0% → 100% | Week 2 |
| **Objective 2**: Validate Multi-Domain | P1.6, B4.3 | 10% → 90% | Week 8 |
| **Objective 3**: Refracto-Path Link | P0.2 | 0% → 100% | Week 2 |
| **Objective 4**: XAI + Clinical Trust | P0.6, P1.3, P1.4, P2.1 | 20% → 95% | Week 12 |
| **Objective 5**: Local Generalization | P0.4, P0.5, P1.5 | 5% → 100% | Week 8 |

**Hypothesis Status**:
- **H1** (Fusion improves AUC): Testable after P0.1 ✓
- **H2** (Refracto-link reduces FPR): Testable after P0.2 ✓
- **H3** (CCR > 85%): Measurable after P0.5 ✓

---

## Immediate Action Items (FIRST 48 HOURS)

### ✅ DONE (This Session)
- [x] Gap analysis: 22 missing, 26 to enhance
- [x] Research alignment: All objectives mapped
- [x] Phase 1 technical spec: All 9 P0 features documented
- [x] Code templates: Fusion, MTL, Audit logger provided

### ⏭️ TODO (Next Session — START HERE)

**1. Set Up Branch Structure** (30 min)
```bash
git checkout -b feature/p0-mtl-architecture
git checkout -b feature/p0-refracto-link
git checkout -b feature/p0-multimodal-ingestion
git checkout -b feature/p0-audit-trail
# ... etc for all 9 P0 features
```

**2. Implement P0.1: Multi-Modal Fusion** (Day 1–2)
- [ ] Create `backend/services/ml_service/core/fusion.py`
- [ ] Create `backend/services/ml_service/core/mtl_model.py`
- [ ] Update `model_loader.py` with MTL loading
- [ ] Write unit tests: `tests/test_fusion.py`
- [ ] Test with dummy fundus + OCT inputs
- [ ] PR review & merge

**3. Implement P0.2: Refracto-Pathological Link** (Day 3)
- [ ] Create `core/refracto_pathological_link.py`
- [ ] Integrate into MTL model
- [ ] Test correction factors on synthetic data
- [ ] Generate example explanations
- [ ] PR review & merge

**4. Implement P0.3 & P0.4: Data Infrastructure** (Day 4–5)
- [ ] Create `imaging_service/multimodal_ingestion.py`
- [ ] Add image quality assessment model
- [ ] Create `patient_service/local_data_manager.py`
- [ ] Add anonymization + consent audit tables
- [ ] Test both pipelines
- [ ] PR review & merge

**5. Implement P0.6: Audit Trail** (Day 6)
- [ ] Create `ml_service/audit_logger.py`
- [ ] Add `PredictionAuditLog` table
- [ ] Hook into inference pipeline
- [ ] Test logging + compliance report generation
- [ ] PR review & merge

**6. Secrets & Security** (Day 7)
- [ ] Create `.env.example` with all secrets
- [ ] Update docker-compose to use Vault (or use local `.env` for now)
- [ ] Remove hardcoded credentials from all files
- [ ] Update CI/CD to not log secrets
- [ ] PR review & merge

---

## Success Metrics (End of Phase 1)

| Metric | Target | Measurement |
|--------|--------|-------------|
| **MTL Fusion Working** | ✓ | Fundus + OCT → fused features → dual outputs |
| **Refracto-Link Active** | ✓ | Glaucoma FPR reduced for myopic cohort |
| **Multi-Modal Data Ingestion** | >95% success rate | 50 test Fundus + OCT pairs processed |
| **CCR Framework Ready** | ✓ Expert panel interface) | 3+ experts can review 5 test cases |
| **Audit Trail Complete** | 100% coverage | Every prediction logged with decision trail |
| **Local Data Collected** | N ≥ 50 | First 50 Sri Lankan patients anonymized |
| **Zero Hardcoded Secrets** | ✓ | All credentials in Vault or `.env.example` |

---

## High-Level Code Map (What Goes Where)

```
backend/services/ml_service/
├── core/
│   ├── fusion.py                          ← [NEW] MultiHeadFusion layer
│   ├── mtl_model.py                       ← [NEW] RefractoMTLModel class
│   ├── refracto_pathological_link.py      ← [NEW] Myopia ↔ Glaucoma linking
│   ├── model_loader.py                    ← [MODIFY] Add MTL loading
│   ├── dataset_loader.py                  ← [ENHANCE] Support triplet loading (fundus, oct, struct)
│   └── preprocessing.py                   ← [KEEP] Extend for multi-modal
├── audit_logger.py                        ← [NEW] Audit trail
├── train_mtl.py                           ← [NEW] MTL training script
└── main.py                                ← [ENHANCE] Add P0 endpoints

backend/services/imaging_service/
├── multimodal_ingestion.py                ← [NEW] Co-registration pipeline
├── models.py                              ← [ADD] ImagePair, ImageQuality tables
└── main.py                                ← [ADD] /upload-multimodal endpoint

backend/services/patient_service/
├── local_data_manager.py                  ← [NEW] Anonymization + consent
├── models.py                              ← [ADD] LocalPatientConsent, DataConsentAudit
└── main.py                                ← [ADD] Local registration endpoints

backend/shared/
└── audit_trail.py                         ← [NEW] Shared audit utilities

frontend/src/components/
└── ClinicalConcordancePanel.tsx           ← [NEW] Expert review UI

frontend/src/pages/
└── ConsentFlow.tsx                        ← [NEW] Privacy/consent workflow
```

---

## Risk Mitigation

| Risk | Severity | Mitigation | Owner |
|------|----------|-----------|-------|
| Data co-registration failures | HIGH | Implement quality thresholds + manual review override | Data Eng |
| Model fusion causes backprop issues | MEDIUM | Unit test gradient flow; use identity shortcut | ML Eng |
| Local data delays (ethics approval) | HIGH | Start Audit Trail in parallel; use synthetic data for testing | Project Mgr |
| Expert panel availability (CCR validation) | HIGH | Recruit panel early; provide async review interface | Clinical Lead |
| Scaling multi-modal ingestion | MEDIUM | Asyncio + batch processing; test with 10K+ pairs | DevOps |

---

## Stakeholder Communication

**To Ethics Committee**:
> "Refracto AI implements comprehensive audit logging (P0.6), anonymization (P0.4), and consent management (P0.9) to meet ethical requirements. Local patient data (N=300–500) will be collected with full informed consent under approval ID: [ETH_APPROVAL_ID]."

**To Clinicians (Expert Panel)**:
> "Your expertise is invaluable for validating our AI system. We're building a structured review interface (P0.5) where you can review AI predictions, provide feedback, and help us measure Clinical Concordance. Compensation: [Details]. Timeline: [Dates]."

**To Development Team**:
> "Phase 1 (4 weeks) focuses on architectural foundations: MTL, fusion, audit trail. We have detailed implementation guides for all 9 P0 features. Week-by-week sprints with PR reviews every 1–2 days."

---

## References & Resources

- **Research Proposal**: See [Proposal] Section 6: Study Design (Two-Phase Approach)
- **Gap Analysis**: See [GAP_ANALYSIS.md](GAP_ANALYSIS.md) (Comprehensive 22 + 26 features)
- **Phase 1 Spec**: See [IMPLEMENTATION_GUIDE_PHASE1.md](IMPLEMENTATION_GUIDE_PHASE1.md) (Detailed code templates)
- **Model Architecture**: See [backend/services/ml_service/core/mtl_model.py](backend/services/ml_service/core/mtl_model.py) (Code provided)
- **Database Schema**: See [backend/services/ml_service/audit_logger.py](backend/services/ml_service/audit_logger.py) (Audit tables)

---

## Next Steps (Prioritized)

### By End of Week 1
1. ✓ Implement Multi-Modal Fusion (P0.1)
2. ✓ Integrate Refracto-Pathological Link (P0.2)
3. ✓ Test MTL model with dummy data
4. ✓ Create PR and merge

### By End of Week 2
5. ✓ Multi-Modal Data Ingestion (P0.3)
6. ✓ Local Data Manager (P0.4)
7. ✓ Database migrations
8. ✓ Integration tests

### By End of Week 3
9. ✓ Audit Trail (P0.6)
10. ✓ CCR Framework (P0.5)
11. ✓ Secrets Management (P0.8)

### By End of Week 4
12. ✓ Consent UI (P0.9)
13. ✓ End-to-end testing
14. ✓ Phase 1 completion & sign-off
15. ✓ Begin Phase 2

---

## Document Control

| Version | Date | Author | Change |
|---------|------|--------|--------|
| 1.0 | 2026-03-12 | System Architect | Initial GA + Phase 1 Guide |
| — | — | — | — |

**Generated by**: AI Assistant (GitHub Copilot)  
**For**: K.M.P. Jayalath, BSc (Hons) Software Engineering  
**Research Project**: Hybrid XAI Clinical Decision Support System for Integrated Ophthalmic Care  

---

**STATUS**: 🟢 READY FOR PHASE 1 DEVELOPMENT

