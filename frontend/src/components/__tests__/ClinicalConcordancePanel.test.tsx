import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { ClinicalConcordancePanel } from '../ClinicalConcordancePanel';
import { mockApiResponses, mockFetchSuccess, resetAllMocks } from '../../tests/setup';

describe('ClinicalConcordancePanel Component', () => {
  const mockPredictions = {
    dr: 'Mild',
    glaucoma: 'Normal',
    refraction: { sphere: -0.50, cylinder: -0.25, axis: 180 },
  };

  beforeEach(() => {
    resetAllMocks();
  });

  it('renders Likert scale for each assessment', () => {
    render(
      <ClinicalConcordancePanel
        patientId="TEST_001"
        predictions={mockPredictions}
      />
    );
    
    expect(screen.getByText(/diabetic retinopathy.*assessment/i)).toBeInTheDocument();
    expect(screen.getByText(/glaucoma.*assessment/i)).toBeInTheDocument();
    expect(screen.getByText(/refraction.*assessment/i)).toBeInTheDocument();
  });

  it('displays all 5 Likert scale options', () => {
    render(
      <ClinicalConcordancePanel
        patientId="TEST_001"
        predictions={mockPredictions}
      />
    );
    
    const likertLabels = screen.getAllByText(
      /strongly disagree|disagree|neutral|agree|strongly agree/i
    );
    expect(likertLabels.length).toBeGreaterThanOrEqual(5);
  });

  it('shows Likert scale descriptions', () => {
    render(
      <ClinicalConcordancePanel
        patientId="TEST_001"
        predictions={mockPredictions}
      />
    );
    
    expect(screen.getByText(/1.*strongly disagree|disagree/i)).toBeInTheDocument();
    expect(screen.getByText(/5.*strongly agree/i)).toBeInTheDocument();
  });

  it('allows selecting Likert scores and highlights selection', async () => {
    const user = userEvent.setup();
    render(
      <ClinicalConcordancePanel
        patientId="TEST_001"
        predictions={mockPredictions}
      />
    );
    
    const agreeButtons = screen.getAllByRole('button').filter(btn => btn.textContent === '4');
    await user.click(agreeButtons[0]);
    
    expect(agreeButtons[0]).toHaveClass('bg-blue-500', 'bg-green-500', 'selected');
  });

  it('requires all three assessments before submission', async () => {
    const user = userEvent.setup();
    mockFetchSuccess({ success: true });
    
    render(
      <ClinicalConcordancePanel
        patientId="TEST_001"
        predictions={mockPredictions}
      />
    );
    
    // Select only one Likert score
    const allButtons = screen.getAllByRole('button');
    const ratingButtons = allButtons.slice(0, 5);
    await user.click(ratingButtons[3]); // Select grade 4
    
    const submitBtn = screen.getByRole('button', { name: /submit/i });
    fireEvent.click(submitBtn);
    
    await waitFor(() => {
      expect(screen.getByText(/please rate all|all three/i)).toBeInTheDocument();
    });
  });

  it('displays clinician ID input field', () => {
    render(
      <ClinicalConcordancePanel
        patientId="TEST_001"
        predictions={mockPredictions}
      />
    );
    
    expect(screen.getByPlaceholderText(/clinician|expert|identifier/i)).toBeInTheDocument();
  });

  it('submits review with complete data', async () => {
    const user = userEvent.setup();
    mockFetchSuccess({ success: true, review_id: 'REV_001' });
    
    const mockOnSubmit = vi.fn();
    render(
      <ClinicalConcordancePanel
        patientId="TEST_001"
        predictions={mockPredictions}
        onReviewSubmitted={mockOnSubmit}
      />
    );
    
    // Select all three Likert scores (4 = agree)
    const allButtons = screen.getAllByRole('button');
    const ratingButtons = allButtons.filter(btn => btn.textContent === '4');
    
    for (let i = 0; i < 3 && i < ratingButtons.length; i++) {
      await user.click(ratingButtons[i]);
    }
    
    // Enter clinician ID
    const clinicianInput = screen.getByPlaceholderText(/clinician|expert/i);
    await user.type(clinicianInput, 'DR_001');
    
    // Submit
    const submitBtn = screen.getByRole('button', { name: /submit/i });
    await user.click(submitBtn);
    
    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/ml/expert-review/submit'),
        expect.any(Object)
      );
    });
  });

  it('displays success message after submission', async () => {
    const user = userEvent.setup();
    mockFetchSuccess({ success: true });
    
    render(
      <ClinicalConcordancePanel
        patientId="TEST_001"
        predictions={mockPredictions}
      />
    );
    
    // Complete form
    const allButtons = screen.getAllByRole('button');
    const ratingButtons = allButtons.filter(btn => btn.textContent === '4');
    for (let i = 0; i < 3; i++) {
      await user.click(ratingButtons[i]);
    }
    
    const clinicianInput = screen.getByPlaceholderText(/clinician/i);
    await user.type(clinicianInput, 'DR_001');
    
    const submitBtn = screen.getByRole('button', { name: /submit/i });
    await user.click(submitBtn);
    
    await waitFor(() => {
      expect(screen.getByText(/submitted|success|thank you/i)).toBeInTheDocument();
    });
  });

  it('shows predictions being reviewed', () => {
    render(
      <ClinicalConcordancePanel
        patientId="TEST_001"
        predictions={mockPredictions}
      />
    );
    
    // Should display the predictions being reviewed
    expect(screen.getByText(/Mild|Normal|-0\.50/)).toBeInTheDocument();
  });

  it('handles API errors gracefully', async () => {
    const user = userEvent.setup();
    mockFetchSuccess({ success: false, error: 'Database error' });
    
    render(
      <ClinicalConcordancePanel
        patientId="TEST_001"
        predictions={mockPredictions}
      />
    );
    
    const allButtons = screen.getAllByRole('button');
    const ratingButtons = allButtons.filter(btn => btn.textContent === '4');
    for (let i = 0; i < 3; i++) {
      await user.click(ratingButtons[i]);
    }
    
    const clinicianInput = screen.getByPlaceholderText(/clinician/i);
    await user.type(clinicianInput, 'DR_001');
    
    const submitBtn = screen.getByRole('button', { name: /submit/i });
    await user.click(submitBtn);
    
    await waitFor(() => {
      expect(screen.getByText(/error|failed/i)).toBeInTheDocument();
    });
  });
});
