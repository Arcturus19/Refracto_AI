import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MultiModalUploader } from '../MultiModalUploader';
import { mockFetchSuccess, mockFetchError, resetAllMocks } from '../../tests/setup';

describe('MultiModalUploader Component', () => {
  beforeEach(() => {
    resetAllMocks();
  });

  it('renders upload interface with both image areas', () => {
    render(<MultiModalUploader />);
    
    expect(screen.getByText(/fundus image/i)).toBeInTheDocument();
    expect(screen.getByText(/oct image/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /analyze/i })).toBeInTheDocument();
  });

  it('shows error when only fundus image uploaded', async () => {
    render(<MultiModalUploader />);
    const user = userEvent.setup();
    
    const fundusFile = new File(['test'], 'fundus.jpg', { type: 'image/jpeg' });
    const fileInputs = screen.getAllByRole('button').filter(btn => btn.textContent?.includes('Browse'));
    
    await user.upload(fileInputs[0], fundusFile);
    
    const analyzeBtn = screen.getByRole('button', { name: /analyze/i });
    fireEvent.click(analyzeBtn);
    
    await waitFor(() => {
      expect(screen.getByText(/both images required/i)).toBeInTheDocument();
    });
  });

  it('enables analyze button only when both images uploaded', async () => {
    render(<MultiModalUploader />);
    const user = userEvent.setup();
    
    const analyzeBtn = screen.getByRole('button', { name: /analyze/i });
    expect(analyzeBtn).toBeDisabled();
    
    const fileInputs = screen.getAllByRole('button').filter(btn => btn.textContent?.includes('Browse'));
    const fundusFile = new File(['test'], 'fundus.jpg', { type: 'image/jpeg' });
    const octFile = new File(['test'], 'oct.jpg', { type: 'image/jpeg' });
    
    await user.upload(fileInputs[0], fundusFile);
    
    expect(analyzeBtn).toBeDisabled();
    
    await user.upload(fileInputs[1], octFile);
    
    await waitFor(() => {
      expect(analyzeBtn).not.toBeDisabled();
    });
  });

  it('displays quality feedback for uploaded images', async () => {
    render(<MultiModalUploader />);
    const user = userEvent.setup();
    
    const fileInputs = screen.getAllByRole('button').filter(btn => btn.textContent?.includes('Browse'));
    const fundusFile = new File(['test'], 'fundus.jpg', { type: 'image/jpeg' });
    
    await user.upload(fileInputs[0], fundusFile);
    
    await waitFor(() => {
      expect(screen.getByText(/quality.*pass/i)).toBeInTheDocument();
    });
  });

  it('calls API endpoint on successful analysis', async () => {
    mockFetchSuccess({ success: true, audit_log_id: 'LOG_001' });
    
    render(<MultiModalUploader />);
    const user = userEvent.setup();
    
    const fileInputs = screen.getAllByRole('button').filter(btn => btn.textContent?.includes('Browse'));
    await user.upload(fileInputs[0], new File(['test'], 'fundus.jpg', { type: 'image/jpeg' }));
    await user.upload(fileInputs[1], new File(['test'], 'oct.jpg', { type: 'image/jpeg' }));
    
    const analyzeBtn = screen.getByRole('button', { name: /analyze/i });
    fireEvent.click(analyzeBtn);
    
    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/ml/analyze/mtl'),
        expect.any(Object)
      );
    });
  });

  it('displays loading state during analysis', async () => {
    (global.fetch as any).mockImplementationOnce(() => new Promise(() => {}));
    
    render(<MultiModalUploader />);
    const user = userEvent.setup();
    
    const fileInputs = screen.getAllByRole('button').filter(btn => btn.textContent?.includes('Browse'));
    await user.upload(fileInputs[0], new File(['test'], 'fundus.jpg', { type: 'image/jpeg' }));
    await user.upload(fileInputs[1], new File(['test'], 'oct.jpg', { type: 'image/jpeg' }));
    
    const analyzeBtn = screen.getByRole('button', { name: /analyze/i });
    fireEvent.click(analyzeBtn);
    
    await waitFor(() => {
      expect(screen.getByText(/analyzing/i)).toBeInTheDocument();
    });
  });

  it('displays error message on API failure', async () => {
    mockFetchError(500, 'Model inference failed');
    
    render(<MultiModalUploader />);
    const user = userEvent.setup();
    
    const fileInputs = screen.getAllByRole('button').filter(btn => btn.textContent?.includes('Browse'));
    await user.upload(fileInputs[0], new File(['test'], 'fundus.jpg', { type: 'image/jpeg' }));
    await user.upload(fileInputs[1], new File(['test'], 'oct.jpg', { type: 'image/jpeg' }));
    
    const analyzeBtn = screen.getByRole('button', { name: /analyze/i });
    fireEvent.click(analyzeBtn);
    
    await waitFor(() => {
      expect(screen.getByText(/error|failed/i)).toBeInTheDocument();
    });
  });

  it('resets form when reset button clicked', async () => {
    render(<MultiModalUploader />);
    const user = userEvent.setup();
    
    const fileInputs = screen.getAllByRole('button').filter(btn => btn.textContent?.includes('Browse'));
    await user.upload(fileInputs[0], new File(['test'], 'fundus.jpg', { type: 'image/jpeg' }));
    await user.upload(fileInputs[1], new File(['test'], 'oct.jpg', { type: 'image/jpeg' }));
    
    const resetBtn = screen.getByRole('button', { name: /reset|clear/i });
    fireEvent.click(resetBtn);
    
    expect(screen.getByRole('button', { name: /analyze/i })).toBeDisabled();
  });

  it('rejects invalid file types', async () => {
    render(<MultiModalUploader />);
    const user = userEvent.setup();
    
    const fileInputs = screen.getAllByRole('button').filter(btn => btn.textContent?.includes('Browse'));
    const invalidFile = new File(['test'], 'document.pdf', { type: 'application/pdf' });
    
    await user.upload(fileInputs[0], invalidFile);
    
    expect(screen.getByText(/invalid.*format|only.*jpg|png/i)).toBeInTheDocument();
  });
});
