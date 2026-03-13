# Week 2 Implementation Guide: Frontend Testing & E2E Validation

**Objective**: Complete frontend unit tests, run API integration tests, and conduct end-to-end testing.

**Timeline**: 7 days  
**Dependencies**: Week 1 completed (P0.1-P0.6 modules + tests)  
**Deliverables**: 80%+ frontend coverage + 56+ API tests passing + E2E workflow validated

---

## Week 2 Monday: Frontend Test Framework Setup

### Task 2.1: Install Test Dependencies

```bash
cd frontend

# Install Vitest + React Testing Library
npm install -D vitest @testing-library/react @testing-library/jest-dom \
  @testing-library/user-event happy-dom @vitest/ui

# Install Mocking libraries
npm install -D msw vitest-mock-extended

# Update package.json scripts
npm set-script test "vitest"
npm set-script test:ui "vitest --ui"
npm set-script test:coverage "vitest --coverage"
```

### Task 2.2: Create Test Configuration (vitest.config.ts)

**File**: `frontend/vitest.config.ts`

```typescript
import { defineConfig } from 'vitest/config';
import react from '@vitejs/plugin-react';
import path from 'path';

export default defineConfig({
  plugins: [react()],
  test: {
    globals: true,
    environment: 'happy-dom',
    setupFiles: ['src/tests/setup.ts'],
    coverage: {
      provider: 'v8',
      reporter: ['text', 'json', 'html'],
      exclude: ['node_modules/', 'src/tests/'],
      lines: 80,
      functions: 80,
      branches: 75,
      statements: 80
    }
  },
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src')
    }
  }
});
```

### Task 2.3: Create Test Setup & Mocking

**File**: `frontend/src/tests/setup.ts`

```typescript
import '@testing-library/jest-dom';
import { expect, afterEach, vi } from 'vitest';
import { cleanup } from '@testing-library/react';

// Cleanup after each test
afterEach(() => {
  cleanup();
});

// Mock API responses
export const mockApiResponses = {
  mtlAnalysis: {
    dr_prediction: {
      class: 'Mild',
      confidence: 0.87,
      class_scores: {
        'No DR': 0.05,
        'Mild': 0.87,
        'Moderate': 0.06,
        'Severe': 0.01,
        'Proliferative': 0.01
      }
    },
    glaucoma_prediction: {
      prediction: 'Normal',
      confidence: 0.92,
      original_logit: 0.523,
      corrected_logit: 0.525,
      correction_factor: 1.003
    },
    refraction_prediction: {
      sphere: -0.50,
      cylinder: -0.25,
      axis: 180,
      confidence: 0.88
    },
    correction_factor: 1.003,
    audit_log_id: 'LOG_TEST_001',
    timestamp: new Date().toISOString()
  },

  ccrMetrics: {
    global_ccr: 0.87,
    h3_hypothesis_status: 'PASS',
    total_cases: 35,
    cases_above_threshold: 30,
    task_specific_ccr: {
      dr_ccr: 0.89,
      glaucoma_ccr: 0.85,
      refraction_ccr: 0.87
    },
    expert_metrics: [
      {
        expert_id: 'DR_001',
        dr_agreement: 0.9,
        glaucoma_agreement: 0.85,
        refraction_agreement: 0.88,
        avg_agreement: 0.88
      }
    ]
  },

  auditLogs: {
    logs: [
      {
        log_id: 'LOG_TEST_001',
        timestamp: new Date().toISOString(),
        anonymized_patient_hash: 'a1b2c3d4e5f6...',
        task: 'DR',
        prediction: 'Mild',
        confidence: 0.87,
        correction_applied: false
      }
    ],
    count: 1
  }
};
```

---

## Week 2 Tuesday-Wednesday: Frontend Component Tests

### Task 2.4: MultiModalUploader Tests

**File**: `frontend/src/components/__tests__/MultiModalUploader.test.tsx`

```typescript
import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MultiModalUploader } from '../MultiModalUploader';

describe('MultiModalUploader', () => {
  it('renders upload interface with both image areas', () => {
    render(<MultiModalUploader />);
    expect(screen.getByText(/fundus image/i)).toBeInTheDocument();
    expect(screen.getByText(/oct image/i)).toBeInTheDocument();
  });

  it('shows error when only one image uploaded', async () => {
    render(<MultiModalUploader />);
    const inputs = screen.getAllByDisplayValue('');
    
    // Upload only fundus
    const fundusFile = new File(['test'], 'fundus.jpg', { type: 'image/jpeg' });
    await userEvent.upload(inputs[0], fundusFile);
    
    // Try to analyze
    const analyzeBtn = screen.getByText(/analyze images/i);
    fireEvent.click(analyzeBtn);
    
    await waitFor(() => {
      expect(screen.getByText(/both images required/i)).toBeInTheDocument();
    });
  });

  it('enables analyze button only with both images', async () => {
    render(<MultiModalUploader />);
    const analyzeBtn = screen.getByText(/analyze images/i);
    
    expect(analyzeBtn).toBeDisabled();
    
    const inputs = screen.getAllByDisplayValue('');
    const fundusFile = new File(['test'], 'fundus.jpg', { type: 'image/jpeg' });
    const octFile = new File(['test'], 'oct.jpg', { type: 'image/jpeg' });
    
    await userEvent.upload(inputs[0], fundusFile);
    await userEvent.upload(inputs[1], octFile);
    
    await waitFor(() => {
      expect(analyzeBtn).not.toBeDisabled();
    });
  });

  it('calls API on successful upload', async () => {
    const mockFetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ success: true })
    });
    global.fetch = mockFetch;
    
    render(<MultiModalUploader />);
    const inputs = screen.getAllByDisplayValue('');
    
    const fundusFile = new File(['test'], 'fundus.jpg', { type: 'image/jpeg' });
    const octFile = new File(['test'], 'oct.jpg', { type: 'image/jpeg' });
    
    await userEvent.upload(inputs[0], fundusFile);
    await userEvent.upload(inputs[1], octFile);
    
    const analyzeBtn = screen.getByText(/analyze images/i);
    fireEvent.click(analyzeBtn);
    
    await waitFor(() => {
      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/ml/analyze/mtl'),
        expect.any(Object)
      );
    });
  });

  it('displays loading state during analysis', async () => {
    const mockFetch = vi.fn(() => new Promise(() => {})); // Never resolves
    global.fetch = mockFetch;
    
    render(<MultiModalUploader />);
    const inputs = screen.getAllByDisplayValue('');
    
    const fundusFile = new File(['test'], 'fundus.jpg', { type: 'image/jpeg' });
    const octFile = new File(['test'], 'oct.jpg', { type: 'image/jpeg' });
    
    await userEvent.upload(inputs[0], fundusFile);
    await userEvent.upload(inputs[1], octFile);
    
    const analyzeBtn = screen.getByText(/analyze images/i);
    fireEvent.click(analyzeBtn);
    
    await waitFor(() => {
      expect(screen.getByText(/analyzing/i)).toBeInTheDocument();
    });
  });
});
```

### Task 2.5: MTLResultsPanel Tests

**File**: `frontend/src/components/__tests__/MTLResultsPanel.test.tsx`

```typescript
import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import { MTLResultsPanel } from '../MTLResultsPanel';
import { mockApiResponses } from '../../tests/setup';

describe('MTLResultsPanel', () => {
  it('displays all three prediction categories', () => {
    render(<MTLResultsPanel predictions={mockApiResponses.mtlAnalysis} />);
    
    expect(screen.getByText(/diabetic retinopathy/i)).toBeInTheDocument();
    expect(screen.getByText(/glaucoma screening/i)).toBeInTheDocument();
    expect(screen.getByText(/predicted refraction/i)).toBeInTheDocument();
  });

  it('shows correct DR classification', () => {
    render(<MTLResultsPanel predictions={mockApiResponses.mtlAnalysis} />);
    expect(screen.getByText('Mild')).toBeInTheDocument(); // DR class
  });

  it('shows correction factor when applied', () => {
    const predictions = {
      ...mockApiResponses.mtlAnalysis,
      glaucoma_prediction: {
        ...mockApiResponses.mtlAnalysis.glaucoma_prediction,
        correction_factor: 0.65 // Myopia correction
      }
    };
    
    render(<MTLResultsPanel predictions={predictions} />);
    expect(screen.getByText(/myopia correction applied/i)).toBeInTheDocument();
    expect(screen.getByText(/0.65/)).toBeInTheDocument();
  });

  it('displays confidence bars for each task', () => {
    render(<MTLResultsPanel predictions={mockApiResponses.mtlAnalysis} />);
    const confidenceBars = screen.getAllByRole('progressbar', { hidden: true });
    expect(confidenceBars.length).toBeGreaterThanOrEqual(3);
  });

  it('shows warning for low confidence predictions', () => {
    const lowConfidence = {
      ...mockApiResponses.mtlAnalysis,
      diabetic_retinopathy: {
        ...mockApiResponses.mtlAnalysis.dr_prediction,
        confidence: 0.62 // Below 0.7 threshold
      }
    };
    
    render(<MTLResultsPanel predictions={lowConfidence} />);
    expect(screen.getByText(/low confidence/i)).toBeInTheDocument();
  });

  it('calls onRequestReview when button clicked', async () => {
    const mockOnRequestReview = vi.fn();
    const { getByText } = render(
      <MTLResultsPanel 
        predictions={mockApiResponses.mtlAnalysis}
        onRequestReview={mockOnRequestReview}
      />
    );
    
    const reviewBtn = screen.getByText(/request expert review/i);
    fireEvent.click(reviewBtn);
    
    expect(mockOnRequestReview).toHaveBeenCalled();
  });
});
```

### Task 2.6: ClinicalConcordancePanel Tests

**File**: `frontend/src/components/__tests__/ClinicalConcordancePanel.test.tsx`

```typescript
import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { ClinicalConcordancePanel } from '../ClinicalConcordancePanel';

describe('ClinicalConcordancePanel', () => {
  const mockPredictions = {
    dr: 'Mild',
    glaucoma: 'Normal',
    refraction: { sphere: -0.50, cylinder: -0.25, axis: 180 }
  };

  it('renders Likert scale for each assessment', () => {
    render(
      <ClinicalConcordancePanel
        patientId="TEST_001"
        predictions={mockPredictions}
      />
    );
    
    expect(screen.getByText(/diabetic retinopathy assessment/i)).toBeInTheDocument();
    expect(screen.getByText(/glaucoma screening assessment/i)).toBeInTheDocument();
    expect(screen.getByText(/refraction accuracy assessment/i)).toBeInTheDocument();
  });

  it('displays all 5 Likert options (1-5)', () => {
    render(
      <ClinicalConcordancePanel
        patientId="TEST_001"
        predictions={mockPredictions}
      />
    );
    
    const buttons = screen.getAllByRole('button');
    const likertButtons = buttons.filter((btn) => /^[1-5]$/.test(btn.textContent));
    expect(likertButtons.length).toBeGreaterThanOrEqual(15); // 3 scales × 5 options
  });

  it('allows selecting Likert scores', async () => {
    render(
      <ClinicalConcordancePanel
        patientId="TEST_001"
        predictions={mockPredictions}
      />
    );
    
    const buttons = screen.getAllByRole('button');
    const button4 = buttons.find((btn) => btn.textContent === '4');
    
    fireEvent.click(button4);
    expect(button4).toHaveClass('bg-blue-500'); // Selected state
  });

  it('requires all three assessments before submission', async () => {
    const mockSubmit = vi.fn();
    render(
      <ClinicalConcordancePanel
        patientId="TEST_001"
        predictions={mockPredictions}
        onSubmitReview={mockSubmit}
      />
    );
    
    // Only select one Likert score
    const buttons = screen.getAllByRole('button');
    fireEvent.click(buttons.find((btn) => btn.textContent === '4'));
    
    const submitBtn = screen.getByText(/submit expert review/i);
    fireEvent.click(submitBtn);
    
    await waitFor(() => {
      expect(screen.getByText(/please rate all three/i)).toBeInTheDocument();
    });
    expect(mockSubmit).not.toHaveBeenCalled();
  });

  it('submits review with all data when complete', async () => {
    const mockSubmit = vi.fn().mockResolvedValue(undefined);
    render(
      <ClinicalConcordancePanel
        patientId="TEST_001"
        predictions={mockPredictions}
        onSubmitReview={mockSubmit}
      />
    );
    
    // Select all Likert scores
    const buttons = screen.getAllByRole('button');
    buttons.forEach((btn, idx) => {
      if (btn.textContent === '4' && idx < 15) {
        fireEvent.click(btn);
      }
    });
    
    // Fill clinician ID
    const idInput = screen.getByPlaceholderText(/clinician identifier/i);
    await userEvent.type(idInput, 'DR_TEST_001');
    
    const submitBtn = screen.getByText(/submit expert review/i);
    fireEvent.click(submitBtn);
    
    await waitFor(() => {
      expect(mockSubmit).toHaveBeenCalledWith(
        expect.objectContaining({
          dr_assessment: 4,
          glaucoma_assessment: 4,
          refraction_assessment: 4,
          clinician_id: 'DR_TEST_001'
        })
      );
    });
  });
});
```

### Task 2.7: CCRPanel Tests

**File**: `frontend/src/components/__tests__/CCRPanel.test.tsx`

```typescript
import { describe, it, expect, vi } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { CCRPanel } from '../CCRPanel';
import { mockApiResponses } from '../../tests/setup';

// Mock fetch
global.fetch = vi.fn();

describe('CCRPanel', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('displays H3 hypothesis status', async () => {
    (global.fetch as any).mockResolvedValue({
      ok: true,
      json: async () => mockApiResponses.ccrMetrics
    });
    
    render(<CCRPanel />);
    
    await waitFor(() => {
      expect(screen.getByText('PASS')).toBeInTheDocument();
    });
  });

  it('shows global CCR percentage', async () => {
    (global.fetch as any).mockResolvedValue({
      ok: true,
      json: async () => mockApiResponses.ccrMetrics
    });
    
    render(<CCRPanel />);
    
    await waitFor(() => {
      expect(screen.getByText(/87\.0%/)).toBeInTheDocument(); // 0.87 * 100
    });
  });

  it('displays FAIL status when CCR < 0.85', async () => {
    const failMetrics = {
      ...mockApiResponses.ccrMetrics,
      global_ccr: 0.72,
      h3_hypothesis_status: 'FAIL'
    };
    
    (global.fetch as any).mockResolvedValue({
      ok: true,
      json: async () => failMetrics
    });
    
    render(<CCRPanel />);
    
    await waitFor(() => {
      expect(screen.getByText('FAIL')).toBeInTheDocument();
    });
  });

  it('shows task-specific CCR breakdown', async () => {
    (global.fetch as any).mockResolvedValue({
      ok: true,
      json: async () => mockApiResponses.ccrMetrics
    });
    
    render(<CCRPanel />);
    
    await waitFor(() => {
      expect(screen.getByText(/diabetic retinopathy/i)).toBeInTheDocument();
      expect(screen.getByText(/glaucoma screening/i)).toBeInTheDocument();
      expect(screen.getByText(/refraction/i)).toBeInTheDocument();
    });
  });

  it('displays expert metrics table', async () => {
    (global.fetch as any).mockResolvedValue({
      ok: true,
      json: async () => mockApiResponses.ccrMetrics
    });
    
    render(<CCRPanel showDetails={true} />);
    
    await waitFor(() => {
      expect(screen.getByText(/expert performance/i)).toBeInTheDocument();
      expect(screen.getByText('DR_001')).toBeInTheDocument();
    });
  });

  it('shows PENDING status for insufficient cases', async () => {
    const pendingMetrics = {
      ...mockApiResponses.ccrMetrics,
      total_cases: 10,
      h3_hypothesis_status: 'PENDING'
    };
    
    (global.fetch as any).mockResolvedValue({
      ok: true,
      json: async () => pendingMetrics
    });
    
    render(<CCRPanel />);
    
    await waitFor(() => {
      expect(screen.getByText('PENDING')).toBeInTheDocument();
    });
  });
});
```

### Task 2.8: AuditTrailDashboard Tests

**File**: `frontend/src/components/__tests__/AuditTrailDashboard.test.tsx`

```typescript
import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { AuditTrailDashboard } from '../AuditTrailDashboard';
import { mockApiResponses } from '../../tests/setup';

global.fetch = vi.fn();

describe('AuditTrailDashboard', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('fetches and displays audit logs', async () => {
    (global.fetch as any).mockResolvedValue({
      ok: true,
      json: async () => mockApiResponses.auditLogs
    });
    
    render(<AuditTrailDashboard />);
    
    await waitFor(() => {
      expect(screen.getByText('Mild')).toBeInTheDocument(); // Prediction
    });
  });

  it('allows filtering by task type', async () => {
    (global.fetch as any).mockResolvedValue({
      ok: true,
      json: async () => mockApiResponses.auditLogs
    });
    
    render(<AuditTrailDashboard />);
    
    await waitFor(() => {
      expect(screen.getByRole('button', { name: /DR/i })).toBeInTheDocument();
    });
    
    const filterBtn = screen.getByRole('button', { name: /glaucoma/i });
    fireEvent.click(filterBtn);
    
    // Should update filtered logs
    expect(global.fetch).toHaveBeenCalledWith(
      expect.stringContaining('task=Glaucoma'),
      expect.any(Object)
    );
  });

  it('displays expandable log details', async () => {
    const expandedLogs = {
      ...mockApiResponses.auditLogs,
      logs: [
        {
          ...mockApiResponses.auditLogs.logs[0],
          clinician_feedback: {
            clinician_id: 'DR_001',
            clinician_agreement: 4,
            clinician_feedback: 'Good prediction'
          }
        }
      ]
    };
    
    (global.fetch as any).mockResolvedValue({
      ok: true,
      json: async () => expandedLogs
    });
    
    render(<AuditTrailDashboard />);
    
    await waitFor(() => {
      const logElements = screen.getAllByText(/mild/i);
      fireEvent.click(logElements[0].closest('div'));
    });
    
    await waitFor(() => {
      expect(screen.getByText(/clinician feedback/i)).toBeInTheDocument();
    });
  });

  it('allows exporting logs for compliance', async () => {
    const mockBlob = new Blob(['csv data']);
    (global.fetch as any).mockResolvedValueOnce({
      ok: true,
      json: async () => mockApiResponses.auditLogs
    }).mockResolvedValueOnce({
      ok: true,
      blob: async () => mockBlob
    });
    
    render(<AuditTrailDashboard />);
    
    await waitFor(() => {
      const exportBtn = screen.getByText(/export \(compliance\)/i);
      fireEvent.click(exportBtn);
    });
    
    expect(global.fetch).toHaveBeenCalledWith(
      expect.stringContaining('/api/ml/audit/export/compliance'),
      expect.any(Object)
    );
  });
});
```

---

## Week 2 Thursday: API Integration Tests

### Task 2.9: Run API Integration Tests

```bash
cd backend/services/ml_service

# Run 56+ API integration tests
python -m pytest tests/test_api_p0_integration.py -v --cov=routes_p0_integration --cov-report=html

# Expected output:
# ===================== 56+ passed, warnings in X.XXs =====================
```

**Key areas tested**:
- P0.1/P0.2: MTL analysis endpoint validation
- P0.3: Image ingestion error handling
- P0.4: Patient registration & consent verification
- P0.5: Expert review submission & CCR calculation
- P0.6: Audit logs retrieval & immutability verification
- E2E: Complete workflow (register → consent → analyze → review → audit)

### Task 2.10: Test Coverage Report

```bash
# Generate coverage report
python -m pytest tests/ --cov=core --cov=routes_p0_integration \
  --cov-report=html --cov-report=term

# Verify 80%+ coverage
# Open htmlcov/index.html to view breakdown
```

---

## Week 2 Friday: End-to-End Testing

### Task 2.11: Local Deployment & E2E Workflow

```bash
# 1. Start all services
cd backend
docker-compose up -d postgres minio redis

# 2. Wait for services (30 seconds)
sleep 30

# 3. Apply migrations
alembic upgrade head

# 4. Start ML service
cd services/ml_service
python main.py &

# 5. Start frontend dev server
cd ../../..
cd frontend
npm run dev &

# 6. Open browser to http://localhost:5173
```

###Task 2.12: Manual E2E Workflow Testing

**Scenario**: Local patient image analysis with expert review

**Step 1: Register Patient**
```bash
curl -X POST http://localhost:8001/api/ml/patient/register/local \
  -H "Content-Type: application/json" \
  -d '{
    "age_bracket": "45-50",
    "diabetes_status": "Type 2",
    "iop_left": 15.2,
    "iop_right": 16.1
  }'

# Note: anonymized_patient_id in response
```

**Step 2: Record Consent**
```bash
curl -X POST http://localhost:8001/api/ml/patient/consent/record \
  -H "Content-Type: application/json" \
  -d '{
    "patient_id": "LOCAL_PATIENT_001",
    "consent_type": "image_analysis",
    "expiry_date": "2026-12-31"
  }'
```

**Step 3: Upload & Analyze Images** (via UI)
- Navigate to http://localhost:5173
- Click "Multi-Modal Image Analysis"
- Upload fundus + OCT images
- Click "Analyze Images"
- Verify 3 predictions display

**Step 4: Submit Expert Review** (via UI)
- Click "Request Expert Review"
- Rate DR: 4 (Agree)
- Rate Glaucoma: 4 (Agree)
- Rate Refraction: 5 (Strongly Agree)
- Enter clinician ID
- Click "Submit Expert Review"

**Step 5: Check CCR Dashboard**
- Navigate to CCR panel
- Verify CCR updated
- Check H3 status (PASS/FAIL/PENDING)

**Step 6: View Audit Trail**
- Navigate to Audit Trail Dashboard
- Filter by patient
- Verify immutable log entry
- Check clinician feedback recorded
- Export CSV (verify no PII)

---

## Week 2 Deliverables Checklist

- [ ] Vitest configuration created
- [ ] Test setup file (mocking, fixtures)
- [ ] 5 frontend component test files (80+ tests total)
- [ ] Frontend tests: 80%+ passing, 80%+ coverage
- [ ] API integration tests: 56+ passing
- [ ] Local E2E workflow: Fully tested
  - [ ] Patient registration
  - [ ] Consent recording
  - [ ] Image analysis
  - [ ] Expert review submission
  - [ ] CCR calculation
  - [ ] Audit log viewing
  - [ ] Compliance export
- [ ] Coverage reports: HTML + terminal output
- [ ] Bug fixes: Any failures addressed
- [ ] Documentation: Test results recorded

---

## Week 2 Validation Criteria

| Criterion | Target | Status |
|-----------|--------|--------|
| Frontend tests | 80+ tests | ⏳ In Progress |
| Coverage | 80%+ | ⏳ In Progress |
| API tests | 56+ passing | ⏳ In Progress |
| E2E scenarios | 7 workflows | ⏳ In Progress |
| Zero regressions | 0 failures | ⏳ In Progress |

---

## Troubleshooting Common Issues

### Issue: Vitest can't find modules
```bash
# Solution: Check vite.config.ts alias
# Ensure: '@': path.resolve(__dirname, './src')
```

### Issue: MockAPI not responding
```bash
# Solution: Check MSW setup in test file
# Ensure: global.fetch mocked before render()
```

### Issue: E2E localhost rejected
```bash
# Solution: Check CORS headers in FastAPI
# Add: Allow-Origin: http://localhost:5173
```

---

**Next**: Week 3 - Research Validation (H1/H2/H3)
