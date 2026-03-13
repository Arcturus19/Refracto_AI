# Refracto AI: Architecture Transformation Diagrams

## Current Architecture (As-Is)

```
┌────────────────────────────────────────────────────────────────────┐
│                        FRONTEND (React + Vite)                     │
│  ┌──────────────┐  ┌─────────────┐  ┌──────────────┐              │
│  │  Dashboard   │  │   Analysis  │  │  PatientList │              │
│  └──────────────┘  └─────────────┘  └──────────────┘              │
│         ↓                   ↓                 ↓                    │
│  ┌─────────────────────────────────────────────────────────────┐  │
│  │              API Service Layer (api.ts)                    │  │
│  │   ├─ authApi (8001) ├─ imagingApi (8003) ├─ mlApi (8004) │  │
│  └─────────────────────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────────────────────┘
                              ↓
┌────────────────────────────────────────────────────────────────────┐
│                   BACKEND MICROSERVICES                            │
├────────────────────────────────────────────────────────────────────┤
│                                                                    │
│  ┌─────────────┐  ┌──────────────┐  ┌──────────────┐             │
│  │ Auth Service│  │Imaging Service│ │ ML Service   │             │
│  │  (8001)     │  │   (8003)      │ │   (8004)     │             │
│  └─────────────┘  └──────────────┘ └──────────────┘             │
│       ↓                  ↓                ↓                       │
│   [User Auth]      [Image Upload]   [Separate Models]           │
│                                        │                         │
│                                   ┌────┴───────────┐             │
│                                   ↓                ↓             │
│                            ┌────────────┐  ┌─────────────┐      │
│                            │ Fundus     │  │ Refraction  │      │
│                            │ Model      │  │ Model       │      │
│                            │(EfficientNet)│ (EfficientNet)│     │
│                            │(DR Grade)  │  │ (Regression)│      │
│                            └────────────┘  └─────────────┘      │
│                                                                    │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │               Shared Infrastructure                        │ │
│  │  ├─ PostgreSQL ├─ MinIO ├─ Docker Compose ├─ CORS      │ │
│  └─────────────────────────────────────────────────────────────┘ │
│                                                                    │
└────────────────────────────────────────────────────────────────────┘

⚠️  KEY GAPS:
    • NO Multi-Modal Fusion (Fundus + OCT isolated)
    • NO Refracto-Pathological linking
    • NO Structured Data integration (Age, IOP, DM)
    • LIMITED XAI (Grad-CAM only; no SHAP)
    • NO Clinical validation metrics
    • NO Local data collection pipeline
    • NO Ethical audit trail
    • HARDCODED secrets in docker-compose
```

---

## Target Architecture (To-Be) — Phase 1 Complete

```
┌────────────────────────────────────────────────────────────────────┐
│                    FRONTEND (React + Vite + Desktop)               │
│ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐                │
│ │  Dashboard   │ │  Analysis    │ │ PatientList  │                │
│ │ (Real-time)  │ │ (Multi-modal)│ │ (Cohorts)    │                │
│ └──────────────┘ └──────────────┘ └──────────────┘                │
│        ↓                ↓                 ↓                        │
│ ┌────────────────────────────────────────────────────────────┐    │
│ │              NEW: Admin & Expert Panels                   │    │
│ │  ├─ Clinical Concordance Review │─ Consent Flow         │    │
│ │  ├─ Bias Monitoring Dashboard   │─ XAI Explanation View │    │
│ └────────────────────────────────────────────────────────────┘    │
│        ↓                                                           │
│ ┌────────────────────────────────────────────────────────────┐    │
│ │              API Service Layer (Enhanced api.ts)          │    │
│ │  ├─ authApi │─ imagingApi │─ mlApi │─ auditApi (NEW)   │    │
│ └────────────────────────────────────────────────────────────┘    │
└────────────────────────────────────────────────────────────────────┘
                              ↓
┌────────────────────────────────────────────────────────────────────┐
│               BACKEND: Integrated Microservices                    │
├────────────────────────────────────────────────────────────────────┤
│                                                                    │
│  Input Layer:                                                      │
│  ┌─────────────────────────────────────────────────────────────┐  │
│  │ Fundus + OCT + Structured Data (Age, IOP, DM, Refraction) │  │
│  │ ↓ MultiModalIngestor (CO-REGISTRATION VALIDATION)         │  │
│  └─────────────────────────────────────────────────────────────┘  │
│                              ↓                                     │
│  Processing Layer:                                                 │
│  ┌──────────────────────────────────────────────────────────┐     │
│  │              *** NEW: UNIFIED MTL MODEL ***              │     │
│  │                                                          │     │
│  │  Fundus Branch      OCT Branch      Structured Data      │     │
│  │ (EfficientNet-B3)  (Vision Trans)        ↓              │     │
│  │          ↓               ↓          [GBM Layer]         │     │
│  │    Features(1000)  Features(768)     Features(64)      │     │
│  │          └───────────┬───────────────────┘              │     │
│  │                      ↓                                  │     │
│  │        [Multi-Head Attention Fusion]                    │     │
│  │              ↓ Fused Features (512)                    │     │
│  │                      ↓                                  │     │
│  │        [Refracto-Pathological Link]  ← CONNECTS myopia │     │
│  │                      ↓                    to glaucoma   │     │
│  │          Corrected Fused Features (512)               │     │
│  │       ┌──────────┬──────────┬──────────┐              │     │
│  │       ↓          ↓          ↓          ↓              │     │
│  │   ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐        │     │
│  │   │ DR     │ │Glaucoma│ │Refract │ │XAI     │        │     │
│  │   │Grade   │ │Risk    │ │Measure │ │Module  │        │     │
│  │   │(5-cls) │ │(Binary)│ │(3-reg) │ │        │        │     │
│  │   └────────┘ └────────┘ └────────┘ └────────┘        │     │
│  │                ↓          ↓          ↓                │     │
│  │         ┌──────────────┬──────────┬──────────┐        │     │
│  │         ↓              ↓          ↓          ↓        │     │
│  │     [Grad-CAM]    [SHAP]  [Confidence]  [Explanation] │     │
│  │     [Heatmap]  [Feature    [Score]      [Text]        │     │
│  │               Importance]                            │     │
│  └──────────────────────────────────────────────────────┘     │
│                              ↓                                   │
│  Output & Validation:                                            │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │         *** NEW: ETHICAL AUDIT TRAIL ***                │   │
│  │  ├─ Logging: timestamp, patient_hash, prediction,       │   │
│  │  │           confidence, XAI_metadata, clinician_action │   │
│  │  │                                                      │   │
│  │  ├─ Clinician Feedback: accepted/rejected/modified     │   │
│  │  │                                                      │   │
│  │  ├─ Clinical Concordance: Expert panel scores (CCR >85%)│   │
│  │  │                                                      │   │
│  │  └─ Compliance Reports: Auto-generated for Ethics Cmte │   │
│  └──────────────────────────────────────────────────────────┘   │
│                              ↓                                   │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │    *** NEW: LOCAL DATA & FINE-TUNING PIPELINE ***        │   │
│  │                                                          │   │
│  │  ├─ Local Patient Registration (Sri Lanka)             │   │
│  │  │  └─ Fully Anonymized ID: SHA256(name+DOB+salt)     │   │
│  │  │                                                      │   │
│  │  ├─ Informed Consent Management                        │   │
│  │  │  ├─ Full Anonymization (age range only)            │   │
│  │  │  ├─ Partial: Month/Year only                       │   │
│  │  │  └─ Full Data: With explicit approval              │   │
│  │  │                                                      │   │
│  │  ├─ Data Usage Audit Log                              │   │
│  │  │  └─ "patient_X used for training" (immutable)      │   │
│  │  │                                                      │   │
│  │  └─ Fine-tuning Module                                │   │
│  │     └─ Phase 2: MTL model fine-tuned on local data    │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                    │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │      ENHANCED Shared Infrastructure                     │   │
│  │  ├─ PostgreSQL (Extended schema: audit, consent)        │   │
│  │  ├─ Vault/Secrets Manager (Credentials encrypted)      │   │
│  │  ├─ MinIO (S3-compatible storage)                       │   │
│  │  ├─ Docker Compose (Updated with security)             │   │
│  │  └─ CORS + Security Headers                            │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                    │
└────────────────────────────────────────────────────────────────────┘

✅ KEY ADDITIONS:
    ✓ Multi-Modal Fusion (Fundus + OCT + Structured)
    ✓ Refracto-Pathological Linking (Myopia → Glaucoma correction)
    ✓ Comprehensive XAI (Grad-CAM + SHAP + Natural Language)
    ✓ Clinical Validation (CCR > 85% target)
    ✓ Local Data Pipeline (Sri Lankan patients, anonymization)
    ✓ Ethical Audit Trail (Immutable prediction logs)
    ✓ Expert Review Interface (Clinical Concordance scoring)
    ✓ Secrets Management (Vault-based credentials)
```

---

## Data Flow: Single Patient Analysis (Current vs Target)

### CURRENT Flow
```
Patient Fundus Upload
    ↓
[ImageUploader.tsx] → POST /upload/{patient_id}
    ↓
[imaging_service/main.py]
    ├─ Store in MinIO
    └─ Save metadata to DB
         ↓
User clicks "Analyze"
    ↓
[AnalysisPage.tsx] → POST /predict/fundus
    ↓
[ml_service/main.py]
    ├─ Load EfficientNet-B3 (Fundus only)
    ├─ Predict DR Grade (0-4)
    ├─ Generate Grad-CAM
    └─ Return results
         ↓
Display Results + Heatmap
    ↓
❌ Missing:
   - OCT analysis
   - Refraction prediction
   - Glaucoma check
   - SHAP explanation
   - Clinician feedback
   - Audit log
```

### TARGET Flow (Phase 1 Complete)
```
Patient Consents to Research
    ↓
[ConsentFlow.tsx] → POST /register-local-patient
    ↓
[patient_service/local_data_manager.py]
    ├─ Anonymize: SHA256(name + DOB + salt)
    └─ Log: "Consent received, Anonymization Level: Full"
         ↓
Upload Fundus + OCT Pair
    ↓
[ImageUploader.tsx] → POST /upload-multimodal/{patient_id}
    ↓
[imaging_service/multimodal_ingestion.py]
    ├─ Parse DICOM (if OCT is DICOM)
    ├─ Quality Assessment (Fundus: 0.95, OCT: 0.92)
    ├─ Co-registration Validation (0.87 confidence)
    ├─ Log: "Image quality checks passed"
    ├─ Store Fundus → MinIO
    ├─ Store OCT → MinIO
    └─ Create ImagePair record linking both
         ↓
User clicks "Analyze with MTL"
    ↓
[AnalysisPage.tsx] → POST /analyze/mtl
    ↓
[ml_service/main.py]
    ├─ Load Unified MTL Model
    │  ├─ Fundus Branch (EfficientNet-B3)
    │  ├─ OCT Branch (Vision Transformer)
    │  └─ Fusion Layer (Multi-Head Attention)
    │
    ├─ Forward Pass:
    │  ├─ Extract Fundus features: (1, 1000)
    │  ├─ Extract OCT features: (1, 768)
    │  ├─ Fuse via Attention: (1, 512)
    │  ├─ Predict DR Grade: (1, 5) logits
    │  ├─ Predict Glaucoma: (1, 1) logit
    │  └─ Predict Refraction: (1, 3) regression
    │
    ├─ Apply Refracto-Pathological Link:
    │  ├─ Extract Sphere: -3.50
    │  ├─ Check if Myopia: Yes
    │  ├─ Calculate Correction: 0.15
    │  └─ Adjust Glaucoma probability down by 15%
    │
    ├─ Generate XAI Reports:
    │  ├─ Grad-CAM Heatmap (fundus regions influencing DR)
    │  ├─ SHAP Values (age, IOP, DM contribution to glaucoma)
    │  └─ Natural Language: "Moderate myopia detected.
    │      Glaucoma prediction adjusted ↓ 15% due to
    │      refractive morphology artifacts."
    │
    ├─ Log Prediction (Audit Trail):
    │  ├─ Timestamp: 2026-03-12 10:30:15 UTC
    │  ├─ Patient Hash: a7f2c9e8e3d5b1a6...
    │  ├─ Model Version: MTL_v1.0
    │  ├─ Predictions: {dr: 2, glaucoma: 0.35, refraction: {...}}
    │  ├─ Confidence: {dr: 0.92, glaucoma: 0.78}
    │  ├─ XAI: {grad_cam_url, shap_json, explanation_text}
    │  ├─ Ethics ID: IEC_2026_OPHTHAL_001
    │  └─ Consent Level: Full
    │
    └─ Return to Frontend
         ↓
[AnalysisPage.tsx] Displays:
    ├─ DR Grade: 2 (Moderate NPDR)
    │  └─ Confidence: 92%
    ├─ Glaucoma Risk: 35% (↓30% due to myopia)
    │  └─ Confidence: 78%
    ├─ Refraction: SPH -3.50 CYL -0.75 × 180°
    └─ Multi-Modal Images with Grad-CAM overlay
         ↓
Clinician Reviews Results
    ↓
[AnalysisPage.tsx] → POST /audit/clinician-action
    ├─ Action: "accepted"
    ├─ Clinician ID Hash: [hashed for privacy]
    └─ Notes: "Agrees with DR Grade 2. Glaucoma adjustment noted."
         ↓
Audit Log Updated:
    ├─ clinician_action: "accepted"
    └─ timestamp: 2026-03-12 10:35:22 UTC
         ↓
Option: Send to Expert Panel for CCR Validation
    ↓
[ClinicalConcordancePanel.tsx]
    ├─ Display: AI Prediction + XAI Report
    ├─ Expert 1 Review: "I agree (5/5), clear presentation"
    ├─ Expert 2 Review: "Agree (4/5), myopia adjustment helpful"
    ├─ Expert 3 Review: "Agree (5/5), excellent Grad-CAM clarity"
    ├─ Calculate CCR: (5+4+5)/15 = 0.93 (93%)
    └─ Log: "CCR recorded for H3 hypothesis validation"
         ↓
✅ Complete Flow with:
   ✓ Multi-modal analysis
   ✓ Refracto-pathological linking
   ✓ Comprehensive XAI
   ✓ Audit trail
   ✓ Clinical validation
   ✓ Ethics compliance
```

---

## Phase Progression Visualization

```
Week 0: Current State
├─ Microservices ✓
├─ Single-modality ML ✓
├─ Basic Auth + Imaging ✓
└─ React Dashboard ✓

Week 1: P0.1 + P0.2
├─ Multi-Modal Fusion ✓
├─ Refracto-Pathological Link ✓
└─ MTL Model Training ✓

Week 2: P0.3 + P0.4
├─ Multi-Modal Ingestion ✓
├─ Local Data Manager ✓
└─ Anonymization ✓

Week 3: P0.5 + P0.6 + P0.8
├─ Clinical Concordance ✓
├─ Audit Trail ✓
└─ Secrets Management ✓

Week 4: P0.7 + P0.9
├─ DB Schema ✓
└─ Consent UI ✓

Phase 1 Complete:
├─ Research Objectives 1–5: 80% coverage
├─ Hypotheses H1–H3: All testable
└─ Ready for Phase 2 (P1 features)

Week 5–8: Phase 2 (Core Features)
├─ Structured Data (P1.1) ✓
├─ SHAP Integration (P1.3) ✓
├─ Natural Language Reports (P1.4) ✓
├─ Multi-stage Training (P1.5) ✓
└─ Comprehensive Metrics (P1.6) ✓

Week 9–12: Phase 3 (Polish)
├─ XAI Dashboard ✓
├─ Bias Monitoring ✓
├─ Performance Optimization ✓
└─ Production Hardening ✓

End State: Full PROPOSAL Implementation
├─ All 5 Objectives 100% ✓
├─ All 3 Hypotheses validated ✓
├─ Local validation (N=300–500) ✓
└─ Clinical Concordance > 85% ✓
```

---

## Database Schema Evolution

### Current Schema (Minimal)
```
users               image_records        patients
├─ id              ├─ id                ├─ id
├─ email           ├─ patient_id        ├─ full_name
├─ password_hash   ├─ image_type        ├─ dob
└─ role            ├─ file_path         ├─ gender
                   ├─ file_size         └─ diabetes_status
                   └─ uploaded_at
```

### Target Schema (Phase 1)
```
Addition 1: Multi-Modal Support
image_pairs
├─ id
├─ patient_id
├─ fundus_id (FK)
├─ oct_id (FK)
├─ pairing_confidence
├─ quality_metadata (JSON)
└─ created_at

Addition 2: Local Data + Consent
local_patient_consent
├─ id
├─ anonymized_patient_id (PK)
├─ consent_level (ENUM: full/partial/none)
├─ consent_signed_at
├─ eth_approval_id
├─ data_usage_logs (JSON)
└─ created_at

data_consent_audit
├─ id
├─ anonymized_patient_id (FK)
├─ action (ENUM: collection/analysis/export)
├─ timestamp
└─ details (JSON)

Addition 3: Prediction Auditing
prediction_audit_logs
├─ id
├─ prediction_id (UNIQUE)
├─ anonymized_patient_hash
├─ model_version
├─ input_modality (JSON)
├─ predictions (JSON)
├─ confidence_scores (JSON)
├─ xai_metadata (JSON)
├─ clinician_action (ENUM)
├─ clinician_id_hash
├─ feedback_flag (ENUM: none/incorrect_dr/...)
├─ ethics_approval_id
├─ consent_level
└─ timestamp

```

---

## Technology Stack: Enhancements Required

| Component | Current | Phase 1 Addition | Purpose |
|-----------|---------|------------------|---------|
| **Fusion** | — | PyTorch: MultiheadAttention | Modality fusion |
| **XAI** | Grad-CAM | + SHAP library | Feature importance |
| **Utilities** | hashlib, io | + pydicom, pandas | DICOM parsing, data ops |
| **Storage** | MinIO (file) | + PostgreSQL (metadata) | Enhanced co-registration tracking |
| **Secrets** | .env (hardcoded) | + HashiCorp Vault | Credential management |
| **Testing** | pytest (minimal) | + fixtures, factories | Comprehensive coverage |
| **Docs** | README | + Runbooks, model cards | Governance |

---

## Summary: Why These Changes Matter

### For Research
- **H1 (Fusion Superiority)**: Can now prove multi-modal > single-modal via AUC comparison
- **H2 (Refracto-Link)**: Can measure FPR reduction in myopic glaucoma subset
- **H3 (CCR Validation)**: Can objectively measure expert agreement with CCR metric

### For Clinicians
- **Trust**: Explicit explanations (Grad-CAM + SHAP) showing which regions/features matter
- **Safety**: Audit trail ensures accountability; clinician can override with documentation
- **Relevance**: Multi-modal + refracto-link addresses real diagnosis complexity

### For Ethics
- **Privacy**: Full anonymization option; immutable audit log for compliance
- **Transparency**: XAI reports justify every decision
- **Accountability**: Structured consent + data usage tracking

---

**Next Steps**: Begin Phase 1 implementation. See [QUICK_ROADMAP.md](QUICK_ROADMAP.md) for first 48 hours action items.

