# System Accuracy Report (All Components)

**Generated**: 2026-03-21  
**Workspace**: Refracto AI (Windows, CPU-only ML)

This report summarizes the **measured model performance** (where available) and **software correctness/quality** signals (tests) for each major component.

## Definitions (what “accuracy” means per component)

- **ML models**: Accuracy/F1/etc. computed on held-out test splits in `training_log.json`.
- **Software components (APIs, services, frontend)**: “Accuracy” is not a meaningful metric by itself; we report **test pass rate** and known blockers. For production readiness, add SLOs (latency, uptime) and clinical validation metrics (CCR, AUC) on real labeled data.

---

## A) ML Model Accuracy (Measured)

### A1) OCT classifier (4-class: CNV/DME/DRUSEN/NORMAL)

**Best run (recommended artifact)**
- Source: `backend/models/oct_baseline_cpu/training_log.json`
- Test accuracy: **0.999**
- Test macro F1: **0.998999996**
- Balanced accuracy: **0.999**
- Test set size: **1000** (250/class)

**Earlier incomplete run (not representative)**
- Source: `backend/models/oct/training_log.json`
- Epochs ran: **1**
- Test accuracy: **0.25**
- Test macro F1: **0.10**

### A2) Fundus classifier (ODIR-5K, 8-label multi-label)

- Source: `backend/models/fundus_odir/training_log.json`
- Checkpoints:
  - `backend/models/fundus_odir/fundus_odir_last.pt` (checkpoint metadata shows `epoch=10`)
  - `backend/models/fundus_odir/fundus_odir_best.pt`

**Val selection metric**
- Best validation macro F1: **0.5159532650**

**Test metrics** (multi-label)
- Exact match ratio (strict “all labels correct”): **0.2989045383**
- Micro F1: **0.5430690245**
- Macro F1: **0.5155690444**
- Test split size: **639**

Notes:
- For multi-label problems, exact-match accuracy is intentionally strict; micro/macro F1 is usually more informative.

---

## B) ML Service Internal Modules (Correctness Validation)

These are the “core pipeline” components (fusion, MTL head, refracto-link, ingestion, local data manager, CCR framework, audit logging).

### B1) Phase 1 unit/integration tests (current run)

- Test suite location: `backend/services/ml_service/tests/`
- Command used:
  - From `backend/services/ml_service`:
    - `python -m pytest -q`

**Result (2026-03-21)**
- **41 passed, 0 failed** (55 warnings)

Notes:
- `backend/services/ml_service/test_api.py` is a **manual live-server smoke test** that calls `localhost:8004`; it is excluded from automated pytest collection via `backend/services/ml_service/pytest.ini`.

### B2) Historical test report (doc)

- Source: `PHASE1_TEST_RESULTS.md`
- Claims: **22/22 passing**

Interpretation:
- The current automated `ml_service` pytest suite is **green** (see B1), and includes the Phase 1 tests.

---

## C) ML Service API Routes (FastAPI Integration Tests)

### C1) API integration test suite (current run)

- Test file: `backend/services/ml_service/tests/test_api_p0_integration.py`
- Requirements to run:
  - `httpx` must be compatible with Starlette TestClient.
  - If `SECRET_KEY` is required by your local config, set it to any value for tests (e.g. `SECRET_KEY=test`).

**Environment pin applied for reproducibility**
- `backend/services/ml_service/requirements.txt` now pins: `httpx==0.27.0` (Starlette 0.35.1 compatibility).

**Command used**
- From `backend/services/ml_service`:
  - `python -m pytest -q tests/test_api_p0_integration.py`

**Result (2026-03-21)**
- **19 passed, 0 failed**

---

## D) Other Backend Services (Auth / Patient / Imaging / DICOM)

Services present under `backend/services/`:
- `auth_service`
- `patient_service`
- `imaging_service`
- `dicom_service`

**Measured accuracy**: Not applicable (non-ML).  
**Automated correctness metrics in repo**:
- No service-specific pytest suites were found under these services (only `ml_service` has a `tests/` directory).

---

## E) Frontend (UI Correctness)

### E1) Frontend unit tests (Vitest)

- Location: `frontend/src/components/__tests__/...`
- Command used:
  - From `frontend`:
    - `npm test`

**Result (2026-03-21)**
- **5 test files passed**
- **66 tests passed (66 total)**

---

## F) System-Level “Accuracy” Gaps (Not Yet Measured)

These are mentioned in architecture/docs but do not have numeric results committed in the repo artifacts:

- **DR / Glaucoma / Refraction clinical performance** for the multi-modal pipeline (AUC, sensitivity/specificity, calibration).
- **Fusion superiority** comparisons (AUC improvements vs single-modal baselines).
- **CCR (Clinical Concordance Rate)** on real expert-reviewed cases (the framework exists; real-world data not recorded here).

Recommended next measurements:
- For **DR/Glaucoma**: AUC + sensitivity at fixed specificity, per-subgroup metrics.
- For **Refraction**: MAE for sphere/cyl/axis, plus clinically relevant thresholds.
- For **end-to-end**: report time-to-result, failure rate, and audit completeness.
