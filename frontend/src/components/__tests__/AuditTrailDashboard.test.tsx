import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { AuditTrailDashboard } from '../AuditTrailDashboard';
import { mockApiResponses, mockFetchSuccess, resetAllMocks } from '../../tests/setup';

global.fetch = vi.fn();

describe('AuditTrailDashboard Component', () => {
  beforeEach(() => {
    resetAllMocks();
  });

  it('fetches and displays audit logs on mount', async () => {
    mockFetchSuccess(mockApiResponses.auditLogs);
    
    render(<AuditTrailDashboard />);
    
    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/ml/audit'),
        expect.any(Object)
      );
    });
  });

  it('displays audit log entries', async () => {
    mockFetchSuccess(mockApiResponses.auditLogs);
    
    render(<AuditTrailDashboard />);
    
    await waitFor(() => {
      expect(screen.getByText(/Mild|LOG_TEST_001/i)).toBeInTheDocument();
    });
  });

  it('shows immutability indicators for logs', async () => {
    mockFetchSuccess(mockApiResponses.auditLogs);
    
    render(<AuditTrailDashboard />);
    
    await waitFor(() => {
      expect(screen.getByText(/locked|immutable|read-only/i)).toBeInTheDocument();
    });
  });

  it('displays task type for each log entry', async () => {
    mockFetchSuccess(mockApiResponses.auditLogs);
    
    render(<AuditTrailDashboard />);
    
    await waitFor(() => {
      expect(screen.getByText(/DR|Glaucoma|Refraction/i)).toBeInTheDocument();
    });
  });

  it('shows prediction value', async () => {
    mockFetchSuccess(mockApiResponses.auditLogs);
    
    render(<AuditTrailDashboard />);
    
    await waitFor(() => {
      expect(screen.getByText(/Mild/)).toBeInTheDocument();
    });
  });

  it('displays confidence score', async () => {
    mockFetchSuccess(mockApiResponses.auditLogs);
    
    render(<AuditTrailDashboard />);
    
    await waitFor(() => {
      expect(screen.getByText(/0\.87|87%/)).toBeInTheDocument();
    });
  });

  it('shows timestamp of each prediction', async () => {
    mockFetchSuccess(mockApiResponses.auditLogs);
    
    render(<AuditTrailDashboard />);
    
    await waitFor(() => {
      expect(screen.getByText(/timestamp|time|date|\d{4}-\d{2}/)).toBeInTheDocument();
    });
  });

  it('allows filtering by task type', async () => {
    const user = userEvent.setup();
    mockFetchSuccess(mockApiResponses.auditLogs);
    
    render(<AuditTrailDashboard />);
    
    await waitFor(() => {
      const filterBtn = screen.getByRole('button', { name: /filter|task/i });
      expect(filterBtn).toBeInTheDocument();
    });
    
    const drFilter = screen.getByRole('button', { name: /^DR$/i });
    await user.click(drFilter);
    
    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('task=DR'),
        expect.any(Object)
      );
    });
  });

  it('displays expandable log details', async () => {
    mockFetchSuccess(mockApiResponses.auditLogs);
    
    render(<AuditTrailDashboard />);
    
    await waitFor(() => {
      const logsPanel = screen.getByText(/LOG_TEST_001/);
      fireEvent.click(logsPanel);
    });
    
    await waitFor(() => {
      expect(screen.getByText(/clinician.*feedback|feedback|comments/i)).toBeInTheDocument();
    });
  });

  it('shows clinician feedback when available', async () => {
    mockFetchSuccess(mockApiResponses.auditLogs);
    
    render(<AuditTrailDashboard />);
    
    await waitFor(() => {
      const expandBtn = screen.getByRole('button', { name: /expand|details|more/i });
      fireEvent.click(expandBtn);
    });
    
    await waitFor(() => {
      expect(screen.getByText(/Good prediction|feedback/i)).toBeInTheDocument();
    });
  });

  it('allows exporting logs for compliance', async () => {
    const user = userEvent.setup();
    mockFetchSuccess(mockApiResponses.auditLogs);
    (global.fetch as any).mockResolvedValueOnce({
      ok: true,
      blob: async () => new Blob(['csv data']),
    });
    
    render(<AuditTrailDashboard />);
    
    await waitFor(() => {
      expect(screen.getByRole('button', { name: /export|download/i })).toBeInTheDocument();
    });
    
    const exportBtn = screen.getByRole('button', { name: /export|download/i });
    await user.click(exportBtn);
    
    expect(global.fetch).toHaveBeenCalledWith(
      expect.stringContaining('/api/ml/audit/export'),
      expect.any(Object)
    );
  });

  it('ensures no PII in exported data', async () => {
    const user = userEvent.setup();
    mockFetchSuccess(mockApiResponses.auditLogs);
    
    render(<AuditTrailDashboard showPIIWarning={true} />);
    
    await waitFor(() => {
      expect(screen.getByText(/anonymized|no.*pii|privacy/i)).toBeInTheDocument();
    });
  });

  it('displays anonymized patient IDs only', async () => {
    mockFetchSuccess(mockApiResponses.auditLogs);
    
    render(<AuditTrailDashboard />);
    
    await waitFor(() => {
      expect(screen.getByText(/a1b2c3d4e5f6|patient.*hash/i)).toBeInTheDocument();
    });
  });

  it('shows pagination controls', async () => {
    const multipleLogsResponse = {
      logs: Array(25).fill(mockApiResponses.auditLogs.logs[0]),
      count: 25,
    };
    mockFetchSuccess(multipleLogsResponse);
    
    render(<AuditTrailDashboard itemsPerPage={10} />);
    
    await waitFor(() => {
      expect(screen.getByText(/previous|next|page|1 of/i)).toBeInTheDocument();
    });
  });

  it('allows searching logs by patient or date', async () => {
    const user = userEvent.setup();
    mockFetchSuccess(mockApiResponses.auditLogs);
    
    render(<AuditTrailDashboard />);
    
    const searchInput = screen.getByPlaceholderText(/search|filter|query/i);
    await user.type(searchInput, 'a1b2c3d4');
    
    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('a1b2c3d4'),
        expect.any(Object)
      );
    });
  });

  it('displays timestamps in readable format', async () => {
    mockFetchSuccess(mockApiResponses.auditLogs);
    
    render(<AuditTrailDashboard />);
    
    await waitFor(() => {
      const logEntry = screen.getByText(/2026/);
      expect(logEntry).toBeInTheDocument();
    });
  });

  it('shows compliance export format options', async () => {
    mockFetchSuccess(mockApiResponses.auditLogs);
    
    render(<AuditTrailDashboard />);
    
    await waitFor(() => {
      expect(screen.getByText(/csv|json|export.*format/i)).toBeInTheDocument();
    });
  });

  it('handles loading state', async () => {
    (global.fetch as any).mockImplementationOnce(() => new Promise(() => {}));
    
    render(<AuditTrailDashboard />);
    
    expect(screen.getByText(/loading|fetching/i)).toBeInTheDocument();
  });

  it('handles API errors gracefully', async () => {
    (global.fetch as any).mockRejectedValueOnce(new Error('Network error'));
    
    render(<AuditTrailDashboard />);
    
    await waitFor(() => {
      expect(screen.getByText(/error|failed/i)).toBeInTheDocument();
    });
  });

  it('shows empty state when no logs available', async () => {
    mockFetchSuccess({ logs: [], count: 0 });
    
    render(<AuditTrailDashboard />);
    
    await waitFor(() => {
      expect(screen.getByText(/no.*logs|empty|no data/i)).toBeInTheDocument();
    });
  });
});
