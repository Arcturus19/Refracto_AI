# Phase 1 Quick Start Guide

## Overview

This guide shows how to build, test, and deploy Refracto AI Phase 1 locally.

---

## Prerequisites

- Python 3.12+
- Docker & Docker Compose
- PostgreSQL 14+
- Git

---

## Setup

### 1. Clone & Install Dependencies

```bash
cd "c:\Users\VICTUS\Desktop\Refracto AI"

# Create virtual environment (if not already created)
python -m venv .venv
.\.venv\Scripts\activate

# Install Python dependencies
pip install -r backend/services/ml_service/requirements.txt
pip install pytest pytest-cov fastapi uvicorn

# Install specific versions for compatibility
pip install numpy<2.0 matplotlib>=3.8.0 pytorch_grad_cam
```

### 2. Start PostgreSQL & Services

```bash
# From backend directory
cd backend

# Start all services (postgres, minio, redis, etc.)
docker-compose up -d

# Wait for services to be healthy
docker-compose ps

# Check logs if needed
docker-compose logs postgres
```

### 3. Run Database Migrations

```bash
# Apply Phase 1 schema changes
cd backend
alembic upgrade head

# Verify schema created
# Check PostgreSQL:
psql -U refracto_user -d refracto_db -c "\dt"
# Should show: local_patient, consent_record, expert_review, ccr_metrics, prediction_audit_log
```

---

## Running Tests

### Backend Unit Tests (22 tests)

```bash
cd "c:\Users\VICTUS\Desktop\Refracto AI\backend\services\ml_service"

# Run P0 module tests (takes ~20s)
python -m pytest tests/test_phase1_complete.py -v --tb=short

# Expected output:
# ====================== 22 passed, 18 warnings in 21.24s ======================
```

### API Integration Tests (56+ tests)

```bash
# Start ML service first
python main.py &

# Wait 5 seconds for service to start

# Run API integration tests
python -m pytest tests/test_api_p0_integration.py -v --tb=short

# Expected: All tests should be ready to run (may need fixtures for auth)
```

### Test Coverage Report

```bash
# Generate coverage report
python -m pytest tests/ --cov=core --cov-report=html

# Open in browser
start htmlcov/index.html
```

---

## Running Services

### Start ML Service (FastAPI)

```bash
cd backend/services/ml_service

# Option 1: Direct run
python main.py

# Option 2: With uvicorn
uvicorn main:app --reload --host 0.0.0.0 --port 8001

# Check health
curl http://localhost:8001/api/ml/health
```

### Start All Services

```bash
cd backend

# Recommended: Use docker-compose for all services
docker-compose up

# Or individually:
docker-compose up postgres minio redis
# (then separately start fastapi services)
```

---

## Testing the API

### Test MTL Analysis (P0.1/P0.2)

```bash
# With Python requests
curl -X POST "http://localhost:8001/api/ml/analyze/mtl" \
  -H "Content-Type: application/json" \
  -d '{
    "fundus_image": "base64_image_data",
    "oct_image": "base64_image_data",
    "patient_id": "LOCAL_TEST_001"
  }'

# With Python script
python -c "
import requests
import base64
from PIL import Image
import io

# Create sample images
fundus = Image.new('RGB', (512, 512), color='red')
oct = Image.new('L', (512, 512), color=128)

# Convert to base64
fundus_b64 = base64.b64encode(io.BytesIO().getvalue()).decode()
oct_b64 = base64.b64encode(io.BytesIO().getvalue()).decode()

# Send request
response = requests.post('http://localhost:8001/api/ml/analyze/mtl', json={
    'fundus_image': fundus_b64,
    'oct_image': oct_b64,
    'patient_id': 'LOCAL_TEST_001'
})

print(response.json())
"
```

### Test Patient Registration (P0.4)

```bash
curl -X POST "http://localhost:8001/api/ml/patient/register/local" \
  -H "Content-Type: application/json" \
  -d '{
    "age_bracket": "45-50",
    "diabetes_status": "Type 2",
    "iop_left": 15.2,
    "iop_right": 16.1
  }'

# Response:
# {
#   "anonymized_patient_id": "a1b2c3d4e5f6...",
#   "status": "registered"
# }
```

### Test Consent Recording (P0.4)

```bash
curl -X POST "http://localhost:8001/api/ml/patient/consent/record" \
  -H "Content-Type: application/json" \
  -d '{
    "patient_id": "LOCAL_TEST_001",
    "consent_type": "image_analysis",
    "expiry_date": "2025-12-31"
  }'
```

### Test Expert Review (P0.5)

```bash
curl -X POST "http://localhost:8001/api/ml/expert-review/submit" \
  -H "Content-Type: application/json" \
  -d '{
    "patient_id": "LOCAL_TEST_001",
    "dr_assessment": 4,
    "glaucoma_assessment": 5,
    "refraction_assessment": 4,
    "clinician_id": "DR_SMITH_001"
  }'
```

### Test CCR (P0.5 - H3)

```bash
# Get global CCR (should show "PENDING" if < 20 reviews)
curl "http://localhost:8001/api/ml/expert-review/ccr/global"

# Response:
# {
#   "global_ccr": 0.92,
#   "h3_hypothesis_status": "PASS",
#   "task_specific_ccr": {...},
#   "expert_metrics": [...]
# }
```

### Test Audit Logs (P0.6)

```bash
# Get all logs
curl "http://localhost:8001/api/ml/audit/logs"

# Filter by patient hash
curl "http://localhost:8001/api/ml/audit/logs?patient_hash=a1b2c3d4e5f6..."

# Filter by date range
curl "http://localhost:8001/api/ml/audit/logs?start_date=2025-01-01&end_date=2025-01-31"

# Export for compliance (CSV)
curl -X POST "http://localhost:8001/api/ml/audit/export/compliance" \
  --output audit_export.csv
```

---

## Frontend Testing

### Start Development Server

```bash
cd frontend

# Install dependencies
npm install

# Start dev server
npm run dev

# Open browser to http://localhost:5173
```

### Component Integration

The React components are ready to be integrated:

1. **MultiModalUploader**: Upload page
2. **MTLResultsPanel**: Results display
3. **ClinicalConcordancePanel**: Expert review form
4. **CCRPanel**: H3 dashboard
5. **AuditTrailDashboard**: Audit viewer

Example integration in a page:

```tsx
import { MultiModalUploader } from '@/components/MultiModalUploader';
import { MTLResultsPanel } from '@/components/MTLResultsPanel';

export function AnalysisPage() {
  const [results, setResults] = useState(null);

  return (
    <div className="space-y-6">
      <MultiModalUploader onAnalysisComplete={setResults} />
      {results && <MTLResultsPanel predictions={results} />}
    </div>
  );
}
```

---

## Database Management

### View Local Patients

```bash
psql -U refracto_user -d refracto_db

# List all registered patients
SELECT id, anonymized_patient_id, age_bracket, diabetes_status FROM local_patient;

# Count patients
SELECT COUNT(*) FROM local_patient;
```

### View Audit Logs

```sql
-- Most recent predictions
SELECT log_id, timestamp, task, prediction, confidence
FROM prediction_audit_log
ORDER BY timestamp DESC
LIMIT 10;

-- Predictions for specific patient
SELECT * FROM prediction_audit_log
WHERE anonymized_patient_hash = 'a1b2c3d4...'
ORDER BY timestamp DESC;

-- Predictions with clinician feedback
SELECT log_id, prediction, clinician_feedback, clinician_agreement
FROM prediction_audit_log
WHERE clinician_id IS NOT NULL
ORDER BY timestamp DESC;
```

### View CCR Metrics

```sql
-- H3 hypothesis status
SELECT global_ccr, h3_hypothesis_status, total_cases, cases_above_threshold
FROM ccr_metrics
ORDER BY last_updated DESC
LIMIT 1;
```

---

## Troubleshooting

### Issue: "numpy.core.multiarray failed to import"

```bash
# Solution: Fix NumPy compatibility
pip install numpy<2.0 matplotlib>=3.8.0

# Verify
python -c "import numpy; print(numpy.__version__)"  # Should be < 2.0
```

### Issue: PostgreSQL Connection Failed

```bash
# Check if postgres is running
docker ps | grep postgres

# If not, start it
docker-compose up -d postgres

# Test connection
psql -U refracto_user -d refracto_db -c "SELECT 1"
```

### Issue: Alembic Migrations Not Found

```bash
# Ensure you're in backend directory
cd backend

# Check migrations exist
ls alembic/versions/

# Run migration
alembic upgrade head

# Verify
alembic current
```

### Issue: Module Import Errors

```bash
# Ensure you're in correct directory
cd backend/services/ml_service

# Check core modules exist
ls -la core/
# Should have: fusion.py, refracto_pathological_link.py, etc.

# Try importing
python -c "from core.fusion import MultiHeadFusion; print('OK')"
```

---

## Development Workflow

### Adding New Features to P1

1. **Create module** in `backend/services/ml_service/core/`
2. **Write tests** in `tests/test_*.py`
3. **Run tests**: `pytest tests/test_*.py -v`
4. **Create API endpoint** in `routes_p0_integration.py` (or new file)
5. **Test API**: `pytest tests/test_api_*.py -v`
6. **Create React component** in `frontend/src/components/`
7. **Integrate in page**: Import and use component
8. **Test UI**: Manual or React Testing Library

### Code Quality

```bash
# Format code
pip install black
black backend/services/ml_service/

# Lint
pip install pylint
pylint backend/services/ml_service/core/

# Type checking
pip install mypy
mypy backend/services/ml_service/
```

---

## Deployment Checklist

- [ ] All unit tests passing (22/22)
- [ ] API integration tests passing
- [ ] Frontend unit tests passing (80%+ coverage)
- [ ] Database migrations applied (`alembic upgrade head`)
- [ ] Environment variables set
- [ ] Docker images built
- [ ] Health check endpoints responding
- [ ] Audit logs displaying correctly
- [ ] CCR calculation verified
- [ ] No PII in audit exports
- [ ] Load testing completed (W4)

---

## Next Steps

### Week 2
- [ ] Run full API integration tests
- [ ] Create frontend unit tests (React Testing Library)
- [ ] Deploy locally for manual E2E testing
- [ ] Begin research data collection (H1/H2/H3)

### Week 3
- [ ] Performance optimization
- [ ] Load testing (1000+ concurrent requests)
- [ ] Enhancements based on feedback

### Week 4
- [ ] Production hardening
- [ ] staging deployment
- [ ] Final validation

---

## Support

For issues, check:
1. Test output: `pytestlog.txt` or terminal
2. Service logs: `docker-compose logs <service>`
3. Database logs: `psql ... -c "SELECT * FROM pg_stat_statements LIMIT 10"`
4. API docs: `http://localhost:8001/docs` (Swagger)

---

*Last Updated: Phase 1 Completion*

