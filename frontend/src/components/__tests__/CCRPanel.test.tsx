import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { CCRPanel } from '../CCRPanel';
import { mockApiResponses, mockFetchSuccess, resetAllMocks } from '../../tests/setup';

global.fetch = vi.fn();

describe('CCRPanel Component', () => {
  beforeEach(() => {
    resetAllMocks();
  });

  it('fetches and displays CCR metrics on mount', async () => {
    mockFetchSuccess(mockApiResponses.ccrMetrics);
    
    render(<CCRPanel />);
    
    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/ml/expert-review/ccr/global'),
        expect.any(Object)
      );
    });
  });

  it('displays H3 hypothesis status', async () => {
    mockFetchSuccess(mockApiResponses.ccrMetrics);
    
    render(<CCRPanel />);
    
    await waitFor(() => {
      expect(screen.getByText(/PASS/)).toBeInTheDocument();
    });
  });

  it('shows global CCR percentage correctly', async () => {
    mockFetchSuccess(mockApiResponses.ccrMetrics);
    
    render(<CCRPanel />);
    
    await waitFor(() => {
      expect(screen.getByText(/87|0\.87/)).toBeInTheDocument();
    });
  });

  it('displays FAIL status when CCR < 0.85', async () => {
    const failMetrics = {
      ...mockApiResponses.ccrMetrics,
      global_ccr: 0.72,
      h3_hypothesis_status: 'FAIL',
    };
    mockFetchSuccess(failMetrics);
    
    render(<CCRPanel />);
    
    await waitFor(() => {
      expect(screen.getByText(/FAIL/)).toBeInTheDocument();
    });
  });

  it('displays PENDING status when insufficient data', async () => {
    const pendingMetrics = {
      ...mockApiResponses.ccrMetrics,
      total_cases: 5,
      h3_hypothesis_status: 'PENDING',
    };
    mockFetchSuccess(pendingMetrics);
    
    render(<CCRPanel />);
    
    await waitFor(() => {
      expect(screen.getByText(/PENDING/)).toBeInTheDocument();
    });
  });

  it('shows total cases reviewed', async () => {
    mockFetchSuccess(mockApiResponses.ccrMetrics);
    
    render(<CCRPanel />);
    
    await waitFor(() => {
      expect(screen.getByText(/35|cases/i)).toBeInTheDocument();
    });
  });

  it('shows cases in agreement count', async () => {
    mockFetchSuccess(mockApiResponses.ccrMetrics);
    
    render(<CCRPanel />);
    
    await waitFor(() => {
      expect(screen.getByText(/30|consensus/i)).toBeInTheDocument();
    });
  });

  it('displays task-specific CCR breakdown', async () => {
    mockFetchSuccess(mockApiResponses.ccrMetrics);
    
    render(<CCRPanel showTaskBreakdown={true} />);
    
    await waitFor(() => {
      expect(screen.getByText(/diabetic retinopathy|DR.*ccr/i)).toBeInTheDocument();
      expect(screen.getByText(/glaucoma.*ccr/i)).toBeInTheDocument();
      expect(screen.getByText(/refraction.*ccr/i)).toBeInTheDocument();
    });
  });

  it('displays CCR for each task', async () => {
    mockFetchSuccess(mockApiResponses.ccrMetrics);
    
    render(<CCRPanel showTaskBreakdown={true} />);
    
    await waitFor(() => {
      expect(screen.getByText(/0\.89|89%/)).toBeInTheDocument(); // DR CCR
      expect(screen.getByText(/0\.85|85%/)).toBeInTheDocument(); // Glaucoma CCR
      expect(screen.getByText(/0\.87|87%/)).toBeInTheDocument(); // Refraction CCR
    });
  });

  it('displays expert performance metrics when expanded', async () => {
    mockFetchSuccess(mockApiResponses.ccrMetrics);
    
    render(<CCRPanel showExpertMetrics={true} />);
    
    await waitFor(() => {
      expect(screen.getByText(/expert|clinician|performance/i)).toBeInTheDocument();
      expect(screen.getByText(/DR_001/)).toBeInTheDocument();
    });
  });

  it('shows expert agreement scores', async () => {
    mockFetchSuccess(mockApiResponses.ccrMetrics);
    
    render(<CCRPanel showExpertMetrics={true} />);
    
    await waitFor(() => {
      expect(screen.getByText(/0\.90|90%/)).toBeInTheDocument(); // DR agreement
      expect(screen.getByText(/0\.85|85%/)).toBeInTheDocument(); // Glaucoma agreement
      expect(screen.getByText(/0\.88|88%/)).toBeInTheDocument(); // Refraction agreement
    });
  });

  it('displays confidence interval', async () => {
    mockFetchSuccess(mockApiResponses.ccrMetrics);
    
    render(<CCRPanel showConfidenceInterval={true} />);
    
    await waitFor(() => {
      expect(screen.getByText(/confidence.*interval|CI/i)).toBeInTheDocument();
      expect(screen.getByText(/0\.82|0\.92/)).toBeInTheDocument();
    });
  });

  it('shows success indicator when CCR >= 0.85', async () => {
    mockFetchSuccess(mockApiResponses.ccrMetrics);
    
    render(<CCRPanel />);
    
    await waitFor(() => {
      expect(screen.getByText(/✓|pass|success|icon/i)).toBeInTheDocument();
    });
  });

  it('shows warning indicator when CCR < 0.85', async () => {
    const failMetrics = {
      ...mockApiResponses.ccrMetrics,
      global_ccr: 0.70,
      h3_hypothesis_status: 'FAIL',
    };
    mockFetchSuccess(failMetrics);
    
    render(<CCRPanel />);
    
    await waitFor(() => {
      expect(screen.getByText(/✗|fail|warning|icon/i)).toBeInTheDocument();
    });
  });

  it('handles loading state properly', async () => {
    (global.fetch as any).mockImplementationOnce(() => new Promise(() => {}));
    
    render(<CCRPanel />);
    
    expect(screen.getByText(/loading|please wait/i)).toBeInTheDocument();
  });

  it('handles fetch errors gracefully', async () => {
    (global.fetch as any).mockRejectedValueOnce(new Error('Network error'));
    
    render(<CCRPanel />);
    
    await waitFor(() => {
      expect(screen.getByText(/error|failed|unable to load/i)).toBeInTheDocument();
    });
  });
});
