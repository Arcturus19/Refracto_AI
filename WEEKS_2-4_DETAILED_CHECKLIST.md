# Refracto AI: Weeks 2-4 Detailed Task Checklist

**Project**: Refracto AI Phase 2-4 Implementation  
**Total Tasks**: 220+ granular items  
**Timeline**: 3 weeks (21 days)  
**Tracking**: Update daily as tasks complete

---

## 📋 WEEK 2: Frontend Testing & E2E Validation (70 tasks)

### Day 1 (Monday): Vitest Setup & Infrastructure

#### Task 2.1: Install Test Dependencies
- [ ] `npm install -D vitest`
- [ ] `npm install -D @testing-library/react`
- [ ] `npm install -D @testing-library/jest-dom`
- [ ] `npm install -D @testing-library/user-event`
- [ ] `npm install -D happy-dom`
- [ ] `npm install -D @vitest/ui`
- [ ] `npm install -D msw`
- [ ] `npm install -D vitest-mock-extended`
- **Verification**: `npm test --help` returns Vitest commands
- **Time Est**: 15 mins

#### Task 2.2: Create vitest.config.ts
- [ ] Create `frontend/vitest.config.ts`
- [ ] Configure test environment (happy-dom)
- [ ] Set up coverage reporter (v8)
- [ ] Set coverage thresholds (80%+)
- [ ] Configure setupFiles path
- [ ] Add path alias (@)
- **Verification**: `npm test -- --help` shows Vitest options
- **Time Est**: 15 mins

#### Task 2.3: Create Test Setup & Mocking
- [ ] Create `frontend/src/tests/setup.ts`
- [ ] Import @testing-library/jest-dom
- [ ] Create afterEach cleanup hook
- [ ] Create mockApiResponses object
  - [ ] mtlAnalysis response structure
  - [ ] ccrMetrics response structure
  - [ ] auditLogs response structure
- [ ] Create mock utility functions
- **Verification**: `npm test` runs without errors
- **Time Est**: 20 mins

### Day 2 (Tuesday): MultiModalUploader & MTLResultsPanel Tests

#### Task 2.4: MultiModalUploader Tests
- [ ] Create `frontend/src/components/__tests__/MultiModalUploader.test.tsx`
- [ ] ☑️ Test: renders upload interface
- [ ] ☑️ Test: shows error with only one image
- [ ] ☑️ Test: enables analyze button with both images
- [ ] ☑️ Test: calls API on successful upload
- [ ] ☑️ Test: displays loading state
- [ ] ☑️ Test: displays error messages
- [ ] ☑️ Test: clears files on reset
- **Verification**: `npm test MultiModalUploader` → 7 passing
- **Time Est**: 45 mins

#### Task 2.5: MTLResultsPanel Tests
- [ ] Create `frontend/src/components/__tests__/MTLResultsPanel.test.tsx`
- [ ] ☑️ Test: displays all three prediction categories
- [ ] ☑️ Test: shows correct DR classification
- [ ] ☑️ Test: shows correction factor when applied
- [ ] ☑️ Test: displays confidence bars
- [ ] ☑️ Test: shows warning for low confidence
- [ ] ☑️ Test: calls onRequestReview callback
- **Verification**: `npm test MTLResultsPanel` → 6 passing
- **Time Est**: 40 mins

### Day 3 (Wednesday): Concordance, CCR & Audit Tests

#### Task 2.6: ClinicalConcordancePanel Tests
- [ ] Create `frontend/src/components/__tests__/ClinicalConcordancePanel.test.tsx`
- [ ] ☑️ Test: renders Likert scale for each assessment
- [ ] ☑️ Test: displays all 5 Likert options
- [ ] ☑️ Test: allows selecting Likert scores
- [ ] ☑️ Test: requires all three assessments
- [ ] ☑️ Test: submits review with all data
- [ ] ☑️ Test: displays clinician ID field
- **Verification**: `npm test ClinicalConcordancePanel` → 6 passing
- **Time Est**: 45 mins

#### Task 2.7: CCRPanel Tests
- [ ] Create `frontend/src/components/__tests__/CCRPanel.test.tsx`
- [ ] ☑️ Test: displays H3 hypothesis status
- [ ] ☑️ Test: shows global CCR percentage
- [ ] ☑️ Test: displays FAIL status when CCR < 0.85
- [ ] ☑️ Test: shows task-specific CCR breakdown
- [ ] ☑️ Test: displays expert metrics table
- [ ] ☑️ Test: shows PENDING status for insufficient cases
- **Verification**: `npm test CCRPanel` → 6 passing
- **Time Est**: 40 mins

#### Task 2.8: AuditTrailDashboard Tests
- [ ] Create `frontend/src/components/__tests__/AuditTrailDashboard.test.tsx`
- [ ] ☑️ Test: fetches and displays audit logs
- [ ] ☑️ Test: allows filtering by task type
- [ ] ☑️ Test: displays expandable log details
- [ ] ☑️ Test: allows exporting logs for compliance
- [ ] ☑️ Test: displays pagination controls
- [ ] ☑️ Test: shows immutability lock icons
- **Verification**: `npm test AuditTrailDashboard` → 6 passing
- **Time Est**: 40 mins

**Daily Check**: All 5 component test files cover 30+ test cases

### Day 4 (Thursday): API Integration Tests

#### Task 2.9: Run API Integration Tests
- [ ] Navigate to `backend/services/ml_service`
- [ ] Run: `python -m pytest tests/test_api_p0_integration.py -v --tb=short`
- [ ] Verify all categories pass:
  - [ ] P0.1/P0.2 tests (8/8 ✓)
  - [ ] P0.3 tests (4/4 ✓)
  - [ ] P0.4 tests (6/6 ✓)
  - [ ] P0.5 tests (8/8 ✓)
  - [ ] P0.6 tests (8/8 ✓)
  - [ ] E2E workflow test (1/1 ✓)
- [ ] Generate coverage report
- [ ] Verify zero regressions
- **Expected Output**: `56 passed, 0 failed in X.XXs`
- **Time Est**: 30 mins

#### Task 2.10: Test Coverage Report
- [ ] Run: `python -m pytest tests/ --cov=core --cov=routes_p0_integration --cov-report=html`
- [ ] Verify coverage ≥80% on:
  - [ ] fusion.py (coverage ≥80%)
  - [ ] refracto_pathological_link.py (coverage ≥80%)
  - [ ] multimodal_ingestion.py (coverage ≥80%)
  - [ ] local_data_manager.py (coverage ≥80%)
  - [ ] clinical_concordance.py (coverage ≥80%)
  - [ ] audit_logger.py (coverage ≥80%)
  - [ ] routes_p0_integration.py (coverage ≥80%)
- [ ] Generate HTML report
- [ ] Document any coverage gaps
- **Verification**: `htmlcov/index.html` shows 80%+
- **Time Est**: 20 mins

### Day 5 (Friday): E2E Workflow Testing

#### Task 2.11: Local Deployment Setup
- [ ] Start PostgreSQL: `docker-compose up -d postgres`
- [ ] Wait 30 seconds for DB ready
- [ ] Apply migrations: `alembic upgrade head`
- [ ] Verify schema created:
  - [ ] local_patient table exists
  - [ ] consent_record table exists
  - [ ] expert_review table exists
  - [ ] ccr_metrics table exists
  - [ ] prediction_audit_log table exists
- [ ] Start Redis: `docker-compose up -d redis`
- [ ] Start MinIO: `docker-compose up -d minio`
- [ ] Start ML service: `cd backend/services/ml_service && python main.py`
- [ ] Start frontend: `cd frontend && npm run dev`
- **Verification**: All services running, no errors
- **Time Est**: 30 mins

#### Task 2.12: Manual E2E Workflow Testing

**Scenario 1: Patient Registration & Anonymization**
- [ ] POST `/api/ml/patient/register/local`
  - [ ] Body: `{"age_bracket": "45-50", "diabetes_status": "Type 2", "iop_left": 15.2, "iop_right": 16.1}`
  - [ ] Response has `anonymized_patient_id` (SHA-256 hash)
  - [ ] Verify no PII in response (only hash)
- [ ] Verify database record created
- [ ] Check hash is 64 characters

**Scenario 2: Consent Recording**
- [ ] POST `/api/ml/patient/consent/record`
  - [ ] Body includes patient_id, consent_type, expiry_date
  - [ ] Response confirms immutable record
- [ ] Verify consent_record table entry
- [ ] Check immutability flag set
- [ ] Try to update → should fail (immutable)

**Scenario 3: Image Upload & Analysis**
- [ ] Via UI: Upload fundus.jpg + oct.jpg
- [ ] UI shows validation feedback (quality scores)
- [ ] Click "Analyze Images"
- [ ] Verify API call: POST `/api/ml/analyze/mtl`
- [ ] Response includes:
  - [ ] dr_prediction with class + confidence
  - [ ] glaucoma_prediction with correction_factor
  - [ ] refraction_prediction with sphere/cylinder
  - [ ] audit_log_id (tracking)
- [ ] Verify prediction audit log created
- [ ] Check immutable log entry

**Scenario 4: Expert Review Submission**
- [ ] Via UI: Expert Panel interface
- [ ] Rate DR prediction: 4 (Agree)
- [ ] Rate Glaucoma prediction: 4 (Agree)
- [ ] Rate Refraction prediction: 5 (Strongly Agree)
- [ ] Enter clinician ID: "DR_001"
- [ ] Click "Submit Expert Review"
- [ ] Verify API call: POST `/api/ml/expert-review/submit`
- [ ] Response confirms review recorded
- [ ] Check expert_review table entry

**Scenario 5: Clinical Concordance Calculation**
- [ ] Navigate to CCR Panel
- [ ] Verify CCR updated after expert review
- [ ] Check H3 status (PASS/PENDING/FAIL)
- [ ] If ≥3 reviews: verify CCR = (agreement_cases / total)
- [ ] Check task-specific breakdown:
  - [ ] DR CCR calculated
  - [ ] Glaucoma CCR calculated
  - [ ] Refraction CCR calculated

**Scenario 6: Audit Trail Viewing**
- [ ] Navigate to Audit Trail Dashboard
- [ ] Verify all predictions listed
- [ ] Filter by task type (DR/Glaucoma/Refraction)
- [ ] Verify no PII in display (only hashes)
- [ ] Click to expand → see clinician feedback
- [ ] Verify immutability lock icon

**Scenario 7: Compliance Export**
- [ ] Click "Export (Compliance)" button
- [ ] Download CSV file
- [ ] Verify CSV contains:
  - [ ] Anonymized hashes (no patient names)
  - [ ] Predictions + confidence
  - [ ] Clinician feedback
  - [ ] Timestamps
- [ ] Open in Excel → verify no sensitive data
- [ ] Confirm can be audited by regulatory body

- **Verification**: All 7 scenarios complete without errors
- **Time Est**: 60 mins

### Week 2 Summary Check
- [ ] All 5 component test files created
- [ ] 30+ frontend tests written
- [ ] 56+ API tests passing
- [ ] 7 E2E workflows validated
- [ ] Coverage report generated (80%+)
- [ ] No regressions in Phase 1 code
- [ ] Documentation: WEEK2_TEST_RESULTS.md created

**Weekly Status**: ✅ All tasks tracked and complete

---

## 📋 WEEK 3: Research Hypothesis Validation (65 tasks)

### Day 1 (Monday): H1 Validation Prep

#### Task 3.1: Prepare H1 Test Dataset
- [ ] Create `backend/services/ml_service/h1_validation.py`
- [ ] Implement `H1ValidationDataset` class
- [ ] Method: `prepare_balanced_test_set()`
  - [ ] Query 10 images per DR class (0-4)
  - [ ] Total: 50 images balanced
- [ ] Method: `compute_h1_metrics()`
  - [ ] Calculate fundus_only_accuracy
  - [ ] Calculate oct_only_accuracy
  - [ ] Calculate fusion_accuracy
  - [ ] Calculate fusion_advantage
- [ ] Verify balanced distribution
- [ ] Document source of each image (RFMiD/GAMMA/local)
- **Verification**: Test dataset loaded, 50 images balanced
- **Time Est**: 45 mins

#### Task 3.2: Run H1 Baselines
- [ ] Create `backend/services/ml_service/h1_inference.py`
- [ ] Implement `H1InferenceEngine` class
- [ ] Load fundus-only baseline model
- [ ] Load OCT-only baseline model
- [ ] Load fusion model
- [ ] Method: `infer_h1_comparison()`
  - [ ] Run all 3 models on test image
  - [ ] Collect predictions
  - [ ] Collect confidence scores
- [ ] Run inference on all 50 images:
  - [ ] Fundus-only predictions (50/50)
  - [ ] OCT-only predictions (50/50)
  - [ ] Fusion predictions (50/50)
- **Verification**: Predictions collected, no errors
- **Time Est**: 30 mins

#### Task 3.3: Statistical Testing for H1
- [ ] Create `backend/services/ml_service/h1_statistics.py`
- [ ] Implement `mcnemar_test_h1()`
- [ ] Calculate b (single correct, fusion wrong)
- [ ] Calculate c (fusion correct, single wrong)
- [ ] Run McNemar exact binomial test
- [ ] Report p-value, test statistic
- [ ] Determine: H1 PASS if p < 0.05 AND fusion_advantage ≥ 0.05
- **Verification**: Statistical test complete, results documented
- **Time Est**: 30 mins

### Day 2 (Tuesday): H1 Results & H2 Setup

#### Task 3.4: H1 Results Documentation
- [ ] Run full H1 pipeline
- [ ] Generate accuracy table:
  - [ ] Fundus-only: XX.X%
  - [ ] OCT-only: YY.Y%
  - [ ] Fusion: ZZ.Z%
  - [ ] Advantage: +A.A%
- [ ] Document McNemar test results
- [ ] Determine H1 status: PASS/FAIL
- [ ] Create H1 report section
- **Verification**: H1 PASS if advantage ≥ 5% (p < 0.05)
- **Time Est**: 20 mins

#### Task 3.5: Prepare H2 High-Myopia Cohort
- [ ] Create `backend/services/ml_service/h2_validation.py`
- [ ] Implement `H2HighMyopiaCohort` class
- [ ] Method: `extract_high_myopia_cohort()`
  - [ ] Filter patients: sphere ≤ -6.0
  - [ ] Stratify by glaucoma label
  - [ ] Balance: ~25 positive, ~25 negative
  - [ ] Target: 50 patients
- [ ] Load glaucoma labels for each
- [ ] Verify cohort composition
- **Verification**: Cohort extracted, 50 patients, balanced
- **Time Est**: 45 mins

#### Task 3.6: H2 FPR Calculation
- [ ] Method: `compute_fpr_metrics()`
  - [ ] FPR_uncorrected = FP / (FP + TN) without correction
  - [ ] FPR_corrected = FP / (FP + TN) with refracto-link
  - [ ] FPR_reduction = (FPR_uncorrected - FPR_corrected) / FPR_uncorrected
  - [ ] Target: ≥20% reduction
- [ ] Run on all 50 high-myopia patients
- [ ] Determine H2 status: PASS/FAIL
- **Verification**: H2 PASS if reduction ≥ 20% (p < 0.05)
- **Time Est**: 30 mins

### Day 3 (Wednesday): H2 Statistics & H3 Setup

#### Task 3.7: Statistical Testing for H2
- [ ] Create `backend/services/ml_service/h2_statistics.py`
- [ ] Implement paired t-test
- [ ] Compare FPR_uncorrected vs FPR_corrected
- [ ] Calculate t-statistic and p-value
- [ ] Verify one-tailed test (t > 0, p < 0.05)
- [ ] Document results
- **Verification**: Paired t-test complete, p-value calculated
- **Time Est**: 25 mins

#### Task 3.8: H3 Expert Panel Setup
- [ ] Create `backend/services/ml_service/h3_validation.py`
- [ ] Implement `H3ExpertPanelSetup` class
- [ ] Contact 5 ophthalmologists (target 3 committed)
  - [ ] [ ] Expert 1 commitment confirmed
  - [ ] [ ] Expert 2 commitment confirmed
  - [ ] [ ] Expert 3 commitment confirmed
- [ ] Collect expert details:
  - [ ] Name, ID, specialty
  - [ ] Experience level
  - [ ] Availability window
- [ ] Method: `register_expert()` - store expert info
- [ ] Method: `prepare_review_cases()`
  - [ ] Stratify by DR class: 10 images per class (50 total)
  - [ ] Include various myopia levels
  - [ ] Mix high/low confidence predictions
- [ ] Create review case list
- **Verification**: Expert panel registered, 50 review cases prepared
- **Time Est**: 45 mins (includes actual expert outreach)

### Day 4 (Thursday): H3 Collection & Results

#### Task 3.9: H3 Expert Review Collection
- [ ] Setup review interface (web or mobile)
- [ ] Each expert reviews cases independently
- [ ] For each case, expert rates 1-5 Likert:
  - [ ] DR prediction assessment
  - [ ] Glaucoma prediction assessment
  - [ ] Refraction accuracy assessment
- [ ] Store reviews via P0.6 AuditLogger
- [ ] Verify immutable recording
- [ ] Collect reviews from all experts: 3 × 50 = 150 reviews
- **Verification**: All 150 reviews recorded, immutable flags set
- **Time Est**: 120 mins (review collection period)

#### Task 3.10: H3 CCR Calculation
- [ ] Implement `calculate_ccr_from_reviews()`
- [ ] For each case, calculate average Likert score across experts
- [ ] Apply threshold: ≥4 = "in agreement"
- [ ] Calculate task-specific CCR:
  - [ ] DR_CCR = cases with avg_dr ≥ 4 / total
  - [ ] Glaucoma_CCR = cases with avg_glaucoma ≥ 4 / total
  - [ ] Refraction_CCR = cases with avg_refraction ≥ 4 / total
- [ ] Calculate global CCR:
  - [ ] Global_CCR = cases with all 3 tasks ≥ 4 / total
- [ ] Determine H3 status: PASS if Global_CCR ≥ 0.85
- **Verification**: H3 PASS if CCR ≥ 0.85
- **Time Est**: 30 mins

### Day 5 (Friday): Results Compilation

#### Task 3.11: Generate Comprehensive Report
- [ ] Create `backend/services/ml_service/hypothesis_validation_report.py`
- [ ] Compile all H1/H2/H3 results
- [ ] Generate JSON report: `hypothesis_validation.json`
  - [ ] H1: status, metrics, p-value
  - [ ] H2: status, metrics, p-value
  - [ ] H3: status, CCR, expert panel details
- [ ] Generate markdown report: `hypothesis_validation.md`
- [ ] Create summary table:
  - [ ] H1: Fusion +A.A% (p=X) - PASS/FAIL
  - [ ] H2: FPR reduction +B.B% (p=Y) - PASS/FAIL
  - [ ] H3: CCR Z.Z% (p=Z) - PASS/FAIL
- [ ] Overall result: All Pass = GREEN, Any Fail = RED
- **Verification**: Both JSON + markdown reports generated
- **Time Est**: 30 mins

#### Task 3.12: Store Results in Database
- [ ] Create Alembic migration: `002_hypothesis_validation_schema.py`
- [ ] Create tables:
  - [ ] h1_validation_results
  - [ ] h2_validation_results
  - [ ] h3_validation_results
- [ ] Insert results:
  - [ ] H1 record (fundus_acc, oct_acc, fusion_acc, advantage)
  - [ ] H2 record (cohort_size, baseline_fpr, corrected_fpr, reduction)
  - [ ] H3 record (global_ccr, expert_count, cases_reviewed, consensus_rate)
- [ ] Apply migration: `alembic upgrade head`
- [ ] Verify records inserted
- **Verification**: All 3 hypothesis results stored in database
- **Time Est**: 30 mins

### Week 3 Summary Check
- [ ] H1 validation complete: PASS/FAIL documented
- [ ] H2 validation complete: PASS/FAIL documented
- [ ] H3 validation complete: PASS/FAIL documented
- [ ] Statistical significance confirmed (p < 0.05)
- [ ] Database updated with results
- [ ] Comprehensive report generated
- [ ] Documentation: WEEK3_HYPOTHESIS_RESULTS.md created

**Weekly Status**: ✅ All hypothesis validation complete

---

## 📋 WEEK 4: Production Hardening & Deployment (85 tasks)

### Day 1 (Monday): Security Hardening

#### Task 4.1: Secrets Management
- [ ] Choose approach: Vault OR environment variables
- **If Vault**:
  - [ ] Setup Vault instance: `vault server -dev`
  - [ ] Enable AppRole auth: `vault auth enable approle`
  - [ ] Create policy: ml-service policy
  - [ ] Create AppRole: ml-service role
  - [ ] Get ROLE_ID and SECRET_ID
- **If Env Vars**:
  - [ ] Create `.env.production` file
  - [ ] Add: DATABASE_URL=postgresql://...
  - [ ] Add: MINIO_ACCESS_KEY=...
  - [ ] Add: JWT_SECRET=(generate via `openssl rand -hex 32`)
  - [ ] Add: REDIS_URL=redis://...
  - [ ] Verify: No secrets in git (check .gitignore)
- [ ] Update `main.py` to load secrets
- [ ] Verify: Secrets loaded without hardcoding
- **Verification**: Secrets loaded successfully at startup
- **Time Est**: 30 mins

#### Task 4.2: Implement JWT Authentication
- [ ] Create `backend/services/auth_service/jwt_handler.py`
- [ ] Implement `JWTHandler` class
- [ ] Method: `create_access_token()`
  - [ ] Generate JWT with 24-hour expiry
  - [ ] Include clinician_id and role in payload
- [ ] Method: `verify_token()`
  - [ ] Decode JWT
  - [ ] Check expiry
  - [ ] Handle invalid/expired tokens
- [ ] Create `get_current_user()` dependency
- [ ] Apply to endpoints:
  - [ ] POST `/api/ml/expert-review/submit` (require JWT)
  - [ ] POST `/api/ml/patient/register/local` (require JWT)
  - [ ] GET `/api/ml/audit/*` (require JWT)
- [ ] Create login endpoint to generate tokens
- **Verification**: Can generate token → use to access protected endpoint
- **Time Est**: 45 mins

#### Task 4.3: Database Encryption & SSL
- [ ] Enable PostgreSQL SSL:
  - [ ] Generate SSL certs for postgres container
  - [ ] OR use managed DB with SSL default
- [ ] Update connection string: `sslmode=require`
- [ ] Test encrypted connection:
  - [ ] `psql -h localhost --sslmode=require ...`
- [ ] For sensitive columns, encrypt via pgcrypto:
  - [ ] `ALTER DATABASE refracto_ai WITH pgcrypto;`
  - [ ] `CREATE EXTENSION IF NOT EXISTS pgcrypto;`
- [ ] Update SQLAlchemy connection args:
  - [ ] pool_pre_ping=True (test connections)
  - [ ] connect_timeout=10
- [ ] Verify: Connection works with SSL
- **Verification**: DB connection established via SSL
- **Time Est**: 30 mins

#### Task 4.4: Input Validation & Rate Limiting
- [ ] Create Pydantic validators on all request models
- [ ] Example: `MedicalImageInput`
  - [ ] Validate fundus_image_path (format + length)
  - [ ] Validate oct_image_path (format + length)
  - [ ] Validate age_bracket (allowed values)
- [ ] Install rate limiting: `pip install fastapi-limiter2`
- [ ] Setup Redis for rate limiter
- [ ] Apply to endpoints:
  - [ ] 100 requests/minute per IP on `/api/ml/analyze/mtl`
  - [ ] 50 requests/minute per IP on `/api/ml/expert-review/submit`
- [ ] Test rate limit:
  - [ ] Send >100 requests in 1 min → get 429 error
- **Verification**: Rate limiting working, validators enforced
- **Time Est**: 40 mins

#### Task 4.5: Docker Image Security
- [ ] Create `Dockerfile.production`:
  - [ ] Use Python 3.11-slim base
  - [ ] Create non-root user (refracto:refracto)
  - [ ] Copy only necessary files
  - [ ] Use multi-stage build (minimize size)
  - [ ] No hardcoded credentials
  - [ ] Health check: `/health` endpoint
- [ ] Build image: `docker build -t ml-service:1.0.0 -f Dockerfile.production .`
- [ ] Security scan:
  - [ ] Install: `npm install -g snyk` or `pip install trivy`
  - [ ] Scan: `docker scan ml-service:1.0.0` or `trivy image ml-service:1.0.0`
  - [ ] Target: Zero critical vulnerabilities
  - [ ] Document any findings
- [ ] Push to registry: `docker push registry.company.com/ml-service:1.0.0`
- **Verification**: Image passes security scan (zero critical)
- **Time Est**: 45 mins

**Daily Check**: Security measures: ✅ Secrets ✅ JWT ✅ Encryption ✅ Validation ✅ Docker

### Day 2 (Tuesday): Performance Optimization

#### Task 4.6: Model Inference Optimization
- [ ] Create `backend/services/ml_service/inference_optimization.py`
- [ ] Implement `OptimizedMLInference` class
- [ ] Load model with optimizations:
  - [ ] model.eval() (disable dropout)
  - [ ] TorchScript tracing (compile to C++)
  - [ ] OR ONNX export (platform-independent)
- [ ] Method: `convert_to_onnx()`
  - [ ] Export PyTorch model to ONNX
  - [ ] Verify ONNX model runs
  - [ ] Compare inference speed: PyTorch vs ONNX
- [ ] Benchmark results:
  - [ ] PyTorch latency: measure with 100 runs, report p50/p95/p99
  - [ ] ONNX latency: measure with 100 runs, report p50/p95/p99
  - [ ] Expected: ONNX 30-40% faster
- [ ] Enable inference caching via Redis
- **Verification**: Inference < 500ms (PyTorch) or < 300ms (ONNX)
- **Time Est**: 45 mins

#### Task 4.7: Database Query Optimization
- [ ] Create `backend/services/ml_service/database_optimization.py`
- [ ] Create strategic indexes:
  - [ ] Index on `LocalPatientRecord.anonymized_patient_id`
  - [ ] Index on `PredictionAuditLog.anonymized_patient_hash`
  - [ ] Index on `PredictionAuditLog.task`
  - [ ] Index on `ExpertReview.patient_hash`
  - [ ] Composite index: (patient_hash, task)
- [ ] Apply indexes: `alembic revision --autogenerate` + `alembic upgrade head`
- [ ] Benchmark queries before/after indexes:
  - [ ] Query: "Get all logs for patient" - measure time
  - [ ] Query: "Get reviews for patient" - measure time
  - [ ] Target: 50%+ faster after indexes
- [ ] Add pagination to list endpoints (limit 100)
- **Verification**: Indexes applied, queries faster
- **Time Est**: 35 mins

#### Task 4.8: Redis Caching Layer
- [ ] Create `backend/shared/redis_cache.py`
- [ ] Implement `RedisCache` class
- [ ] Decorator: `@cache_result()` for expensive operations
- [ ] Cache targets:
  - [ ] `get_ccr_metrics()` - cache 1 hour (changes infrequently)
  - [ ] `get_patient_reviews()` - cache 30 mins
  - [ ] `get_audit_logs()` - cache 5 mins (changes frequently)
- [ ] Invalidation logic:
  - [ ] Clear CCR cache on new expert review
  - [ ] Clear patient cache on new prediction
  - [ ] Auto-expire via TTL
- [ ] Test caching:
  - [ ] Call function twice, measure second call faster
  - [ ] Manually invalidate, verify fresh computation
- **Verification**: Cache working, second calls faster (measure p50 improvement)
- **Time Est**: 35 mins

**Daily Check**: Performance: ✅ Inference < 500ms ✅ Caching ✅ Indexes

### Day 3 (Wednesday): Infrastructure & Kubernetes

#### Task 4.9: Create Kubernetes Manifests
- [ ] Create `backend/k8s/deployment.yml`
  - [ ] Replicas: 3 (high availability)
  - [ ] Image: ml-service:1.0.0
  - [ ] Resource requests: 2 CPU, 4Gi memory
  - [ ] Resource limits: 4 CPU, 8Gi memory
  - [ ] GPU: 1 (if available)
  - [ ] Health checks: liveness + readiness probes
  - [ ] Security: non-root user, read-only filesystem
  - [ ] Env vars: from secrets
- [ ] Create `backend/k8s/service.yml`
  - [ ] Type: ClusterIP
  - [ ] Port: 8001
- [ ] Create `backend/k8s/hpa.yml` (HorizontalPodAutoscaler)
  - [ ] Min replicas: 3
  - [ ] Max replicas: 10
  - [ ] Target CPU: 70%
  - [ ] Target memory: 80%
- [ ] Create `backend/k8s/secrets.yaml`
  - [ ] DATABASE_URL
  - [ ] MINIO_ACCESS_KEY
  - [ ] JWT_SECRET
- [ ] **Don't commit**: secrets.yaml (use sealed-secrets or Vault)
- **Verification**: Manifests created, syntax valid (validate via kubectl)
- **Time Est**: 50 mins

#### Task 4.10: Staging Deployment
- [ ] Create namespace: `kubectl create namespace refracto-ai-staging`
- [ ] Create secrets:
  - [ ] `kubectl create secret generic ml-secrets --from-literal=db-url=$DATABASE_URL_STAGING ...`
- [ ] Create configmap:
  - [ ] `kubectl create configmap ml-config --from-literal=redis-url=redis://redis-staging:6379`
- [ ] Apply manifests:
  - [ ] `kubectl apply -f backend/k8s/deployment.yml -n refracto-ai-staging`
  - [ ] `kubectl apply -f backend/k8s/service.yml -n refracto-ai-staging`
  - [ ] `kubectl apply -f backend/k8s/hpa.yml -n refracto-ai-staging`
- [ ] Wait for rollout: `kubectl rollout status deployment/ml-service -n refracto-ai-staging`
- [ ] Verify 3 pods running: `kubectl get pods -n refracto-ai-staging`
- [ ] Port forward: `kubectl port-forward -n refracto-ai-staging svc/ml-service 8001:8001`
- [ ] Health check: `curl http://localhost:8001/health` → 200 OK
- [ ] Check logs: `kubectl logs deployment/ml-service -n refracto-ai-staging`
- **Verification**: 3 pods running, service accessible, health check passing
- **Time Est**: 45 mins

**Daily Check**: Infrastructure: ✅ K8s manifests created ✅ Staging deployed

### Day 4 (Thursday): Load Testing & Monitoring

#### Task 4.11: Setup Monitoring
- [ ] Create `backend/k8s/prometheus.yml`
  - [ ] Scrape config for ml-service
  - [ ] Metrics gathered:
    - [ ] http_request_duration_seconds (latency)
    - [ ] http_requests_total (throughput)
    - [ ] gpu_utilization_percent
    - [ ] memory_usage_bytes
    - [ ] model_inference_duration_seconds
- [ ] Deploy Prometheus:
  - [ ] `kubectl apply -f backend/k8s/prometheus-deployment.yml -n refracto-ai-staging`
  - [ ] Verify running: `kubectl get pods -l app=prometheus -n refracto-ai-staging`
- [ ] Port forward: `kubectl port-forward -n refracto-ai-staging svc/prometheus 9090:9090`
- [ ] Check Prometheus UI: `http://localhost:9090`
  - [ ] Targets: ml-service UP
  - [ ] Graphs: metric data flowing
- **Verification**: Prometheus collecting metrics from ml-service
- **Time Est**: 30 mins

#### Task 4.12: Load Testing
- [ ] Prepare load test script: `backend/k8s/load-test.js` (k6 format)
- [ ] Load test stages:
  - [ ] Ramp-up: 0 → 100 VUs over 2 mins
  - [ ] Sustained: 100 VUs for 5 mins
  - [ ] Ramp-down: 100 → 0 VUs over 2 mins
- [ ] Run load test:
  - [ ] `k6 run backend/k8s/load-test.js --vus 100 --duration 10m`
  - [ ] Monitor metrics in Prometheus dashboard
- [ ] Collect results:
  - [ ] p50 latency: target < 200ms ✓
  - [ ] p95 latency: target < 1s ✓
  - [ ] p99 latency: target < 2s ✓
  - [ ] Error rate: target < 1% ✓
  - [ ] Throughput: target > 100 req/sec ✓
- [ ] Document results in test report
- [ ] If targets missed:
  - [ ] Increase replicas (HPA should auto-scale)
  - [ ] Optimize slow queries
  - [ ] Check GPU bottleneck
- **Verification**: Load test complete, targets met (or documented gap)
- **Time Est**: 60 mins

**Daily Check**: Monitoring: ✅ Prometheus running ✅ Load test complete

### Day 5 (Friday): Documentation & Handoff

#### Task 4.13: Create Production Runbooks
- [ ] Create `docs/DEPLOYMENT_RUNBOOK.md`
  - [ ] Pre-deployment checks
  - [ ] Step-by-step deployment
  - [ ] Smoke test procedures
  - [ ] Rollback procedures
- [ ] Create `docs/INCIDENT_RESPONSE.md`
  - [ ] Alert → Investigation → Resolution procedures
  - [ ] For: Service down, high latency, data breach
  - [ ] Escalation contacts
  - [ ] Recovery RPO/RTO
- [ ] Create `docs/MONITORING_GUIDE.md`
  - [ ] Key metrics to watch
  - [ ] Alert thresholds
  - [ ] Dashboard setup
- [ ] Create `docs/API_DOCUMENTATION.md` (Swagger)
  - [ ] All 10 endpoints documented
  - [ ] Request/response examples
  - [ ] Error codes
- [ ] Create `docs/ARCHITECTURE_DIAGRAM.md`
  - [ ] System architecture (ASCII or mermaid)
  - [ ] Data flow diagram
  - [ ] Deployment topology

#### Task 4.14: Final Checklist & Sign-off
- [ ] Code review: All PRs approved
- [ ] Security audit: ✅ PASS (OWASP A+)
- [ ] Performance baseline: ✅ Load test complete
- [ ] H1/H2/H3 validation: ✅ All PASS
- [ ] Disaster recovery test: ✅ RTO < 1 hour
- [ ] Staff training: ✅ Ops team briefed
- [ ] Legal/compliance: ✅ HIPAA verified
- [ ] Go-live approval: ✅ Stakeholders signed off
- [ ] Create `PRODUCTION_READINESS_CHECKLIST.md` with all items checked
- [ ] Schedule production deployment (next available window)
- **Verification**: All checklist items complete, sign-off obtained

**Weekly Status**: ✅ Production-ready, staging live, ready for go-live

---

## 🎯 Final Verification (End of Week 4)

### Code Quality
- [ ] Frontend: 80+ tests, 80%+ coverage
- [ ] Backend: 78+ tests (22 Phase 1 + 56 API), 80%+ coverage
- [ ] Zero linting errors
- [ ] Type checking: 100% (TypeScript + Python)

### Functionality
- [ ] 7 E2E workflows: 7/7 ✓
- [ ] All 10 API endpoints: 10/10 ✓
- [ ] All 5 React components: 5/5 ✓
- [ ] All 6 ML modules: 6/6 ✓

### Research Validation
- [ ] H1: Fusion superiority PASS (or FAIL documented)
- [ ] H2: Refracto-link effectiveness PASS (or FAIL documented)
- [ ] H3: Clinical concordance PASS (or FAIL documented)
- [ ] Statistical significance: p < 0.05 on all PASS

### Production Readiness
- [ ] Security: A+ OWASP score
- [ ] Performance: p99 < 2s, > 100 req/sec
- [ ] Reliability: 99.5% uptime (via SLA)
- [ ] Deployment: Staging live, docs complete
- [ ] Monitoring: Prometheus + alerts configured
- [ ] Backup: RTO < 1 hour, data protected

### Sign-off
- [ ] Project Lead: ✍️ Approved
- [ ] Technical Lead: ✍️ Approved
- [ ] DevOps Lead: ✍️ Approved
- [ ] Domain Expert: ✍️ Approved

---

## 📊 Final Metrics Dashboard

| Component | Target | Status | Notes |
|-----------|--------|--------|-------|
| Phase 1 Completion | 100% | ✅ | All modules + tests |
| Frontend Tests | 80+ | ⏳ | In progress (Week 2) |
| API Tests | 56+ | ⏳ | In progress (Week 2) |
| E2E Workflows | 7/7 | ⏳ | In progress (Week 2) |
| H1 Validation | PASS | ⏳ | In progress (Week 3) |
| H2 Validation | PASS | ⏳ | In progress (Week 3) |
| H3 Validation | PASS | ⏳ | In progress (Week 3) |
| Security Score | A+ | ⏳ | In progress (Week 4) |
| Inference Latency | < 500ms | ⏳ | In progress (Week 4) |
| Staging Deployed | YES | ⏳ | In progress (Week 4) |
| Production Ready | YES | ⏳ | In progress (Week 4) |

---

**Updates**: Refresh daily as tasks complete  
**Current Week**: Week 2, Day [X]  
**Overall Progress**: [ % Complete]  

