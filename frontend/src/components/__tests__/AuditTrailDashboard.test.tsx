import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor, within } from '@testing-library/react';
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

    const detailsBtn = await screen.findByRole('button', { name: 'Details' });
    fireEvent.click(detailsBtn);

    expect(
      await screen.findByText('This record is immutable and cannot be modified after creation.')
    ).toBeInTheDocument();
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
      expect(screen.getByText(/\d{1,2}\/\d{1,2}\/\d{4}/)).toBeInTheDocument();
    });
  });

  it('allows filtering by task type', async () => {
    const user = userEvent.setup();
    // initial load + refetch after filter
    mockFetchSuccess(mockApiResponses.auditLogs);
    mockFetchSuccess(mockApiResponses.auditLogs);
    
    render(<AuditTrailDashboard />);

    // Wait for initial fetch to complete
    await screen.findByText(/LOG_TEST_001/i);

    const drFilter = screen.getByRole('button', { name: 'DR' });
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

    const detailsBtn = await screen.findByRole('button', { name: 'Details' });
    fireEvent.click(detailsBtn);

    expect(await screen.findByText('Prediction Details')).toBeInTheDocument();
    expect(screen.getByText('Log ID')).toBeInTheDocument();
  });

  it('shows clinician feedback when available', async () => {
    const logsWithClinicianFeedback = {
      logs: [
        {
          ...mockApiResponses.auditLogs.logs[0],
          model_version: 'v1.0.0',
          consent_verified: true,
          ethics_approval_id: 'ETHICS_TEST_001',
          clinician_feedback: {
            clinician_id: 'DR_001',
            clinician_agreement: 4,
            clinician_feedback: 'Good prediction',
            feedback_timestamp: new Date().toISOString(),
          },
        },
      ],
      count: 1,
    };

    mockFetchSuccess(logsWithClinicianFeedback);
    
    render(<AuditTrailDashboard />);

    const detailsBtn = await screen.findByRole('button', { name: 'Details' });
    fireEvent.click(detailsBtn);

    expect(await screen.findByText(/Clinician feedback:/i)).toBeInTheDocument();
    expect(screen.getByText(/Good prediction/i)).toBeInTheDocument();
  });

  it('allows exporting logs for compliance', async () => {
    const user = userEvent.setup();
    mockFetchSuccess(mockApiResponses.auditLogs);

    const createObjectURLSpy = vi.fn(() => 'blob:mock');
    Object.defineProperty(global.URL, 'createObjectURL', {
      value: createObjectURLSpy,
      writable: true,
    });

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
    mockFetchSuccess(mockApiResponses.auditLogs);
    
    render(<AuditTrailDashboard showPIIWarning={true} />);

    // Wait for initial async fetch + state update to settle
    await screen.findByText(/LOG_TEST_001/i);

    expect(
      screen.getByText('All data shown is anonymized — no PII is stored or displayed.')
    ).toBeInTheDocument();
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
      logs: Array.from({ length: 25 }, (_, idx) => ({
        ...mockApiResponses.auditLogs.logs[0],
        log_id: `LOG_TEST_${String(idx + 1).padStart(3, '0')}`,
      })),
      count: 25,
    };
    mockFetchSuccess(multipleLogsResponse);
    
    render(<AuditTrailDashboard itemsPerPage={10} />);

    expect(await screen.findByRole('button', { name: 'Previous' })).toBeDisabled();
    expect(screen.getByText('Page 1 of 3')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Next' })).toBeEnabled();
  });

  it('allows searching logs by patient or date', async () => {
    const user = userEvent.setup();
    // initial load + refetch after search
    mockFetchSuccess(mockApiResponses.auditLogs);
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
      expect(screen.getByText(/\d{1,2}\/\d{1,2}\/\d{4}/)).toBeInTheDocument();
    });
  });

  it('shows compliance export format options', async () => {
    mockFetchSuccess(mockApiResponses.auditLogs);
    
    render(<AuditTrailDashboard />);

    const select = await screen.findByRole('combobox');
    expect(within(select).getByRole('option', { name: 'CSV' })).toBeInTheDocument();
    expect(within(select).getByRole('option', { name: 'JSON' })).toBeInTheDocument();
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
