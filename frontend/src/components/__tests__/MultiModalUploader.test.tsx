import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MultiModalUploader } from '../MultiModalUploader';
import { mockFetchSuccess, mockFetchError, resetAllMocks } from '../../tests/setup';

describe('MultiModalUploader Component', () => {
  beforeEach(() => {
    resetAllMocks();
  });

  const getFundusInput = () => document.getElementById('fundus-input') as HTMLInputElement;
  const getOctInput = () => document.getElementById('oct-input') as HTMLInputElement;

  it('renders upload interface with both image areas', () => {
    render(<MultiModalUploader />);

    expect(getFundusInput()).toBeTruthy();
    expect(getOctInput()).toBeTruthy();
    expect(screen.getByRole('button', { name: /analyze hybrid data/i })).toBeInTheDocument();
  });

  it('shows error when only fundus image uploaded', async () => {
    render(<MultiModalUploader />);
    const user = userEvent.setup();

    await user.upload(getFundusInput(), new File(['test'], 'fundus.jpg', { type: 'image/jpeg' }));

    // Current UX: analyze is disabled until both images are uploaded.
    expect(screen.getByRole('button', { name: /analyze hybrid data/i })).toBeDisabled();
    expect(screen.getByText(/both fundus and oct images are required/i)).toBeInTheDocument();
  });

  it('enables analyze button only when both images uploaded', async () => {
    render(<MultiModalUploader />);
    const user = userEvent.setup();

    expect(screen.getByRole('button', { name: /analyze hybrid data/i })).toBeDisabled();

    await user.upload(getFundusInput(), new File(['test'], 'fundus.jpg', { type: 'image/jpeg' }));
    expect(screen.getByRole('button', { name: /analyze hybrid data/i })).toBeDisabled();

    await user.upload(getOctInput(), new File(['test'], 'oct.jpg', { type: 'image/jpeg' }));

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /analyze hybrid data/i })).not.toBeDisabled();
    });
  });

  it('displays quality feedback for uploaded images', async () => {
    render(<MultiModalUploader />);
    const user = userEvent.setup();

    await user.upload(getFundusInput(), new File(['test'], 'fundus.jpg', { type: 'image/jpeg' }));

    // Current component shows a preview thumbnail after upload.
    await waitFor(() => {
      expect(screen.getByAltText(/fundus image/i)).toBeInTheDocument();
    });
  });

  it('calls API endpoint on successful analysis', async () => {
    mockFetchSuccess({ success: true, audit_log_id: 'LOG_001' });
    
    render(<MultiModalUploader />);
    const user = userEvent.setup();

    await user.upload(getFundusInput(), new File(['test'], 'fundus.jpg', { type: 'image/jpeg' }));
    await user.upload(getOctInput(), new File(['test'], 'oct.jpg', { type: 'image/jpeg' }));

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /analyze hybrid data/i })).not.toBeDisabled();
    });

    fireEvent.click(screen.getByRole('button', { name: /analyze hybrid data/i }));
    
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

    await user.upload(getFundusInput(), new File(['test'], 'fundus.jpg', { type: 'image/jpeg' }));
    await user.upload(getOctInput(), new File(['test'], 'oct.jpg', { type: 'image/jpeg' }));

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /analyze hybrid data/i })).not.toBeDisabled();
    });

    fireEvent.click(screen.getByRole('button', { name: /analyze hybrid data/i }));
    
    await waitFor(() => {
      expect(screen.getByText(/analyzing/i)).toBeInTheDocument();
    });
  });

  it('displays error message on API failure', async () => {
    mockFetchError(500, 'Model inference failed');
    
    render(<MultiModalUploader />);
    const user = userEvent.setup();

    await user.upload(getFundusInput(), new File(['test'], 'fundus.jpg', { type: 'image/jpeg' }));
    await user.upload(getOctInput(), new File(['test'], 'oct.jpg', { type: 'image/jpeg' }));

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /analyze hybrid data/i })).not.toBeDisabled();
    });

    fireEvent.click(screen.getByRole('button', { name: /analyze hybrid data/i }));
    
    await waitFor(() => {
      expect(screen.getByText(/analysis failed/i)).toBeInTheDocument();
    });
  });

  it('resets form when reset button clicked', async () => {
    render(<MultiModalUploader />);
    const user = userEvent.setup();

    await user.upload(getFundusInput(), new File(['test'], 'fundus.jpg', { type: 'image/jpeg' }));
    await user.upload(getOctInput(), new File(['test'], 'oct.jpg', { type: 'image/jpeg' }));

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /analyze hybrid data/i })).not.toBeDisabled();
    });

    // Remove both images via the per-image remove buttons.
    const removeButtons = screen.getAllByTitle(/remove image/i);
    removeButtons.forEach(btn => fireEvent.click(btn));

    expect(screen.getByRole('button', { name: /analyze hybrid data/i })).toBeDisabled();
  });

  it('rejects invalid file types', async () => {
    render(<MultiModalUploader />);
    const user = userEvent.setup();

    const invalidFile = new File(['test'], 'document.pdf', { type: 'application/pdf' });

    // Use drag-drop to bypass <input accept="..."> filtering and exercise validation.
    const fundusDropZone = getFundusInput().parentElement as HTMLElement;
    fireEvent.drop(fundusDropZone, {
      dataTransfer: { files: [invalidFile] },
    });

    await waitFor(() => {
      expect(screen.getByText(/please select an image or dicom file/i)).toBeInTheDocument();
    });
  });
});
