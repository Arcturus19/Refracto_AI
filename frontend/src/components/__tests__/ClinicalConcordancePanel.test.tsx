import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { ClinicalConcordancePanel } from '../ClinicalConcordancePanel';
import { mockFetchSuccess, resetAllMocks } from '../../tests/setup';

const selectLikertScore = async (user: ReturnType<typeof userEvent.setup>, scaleLabel: RegExp, score: number) => {
  const labelNode = screen.getByText(scaleLabel);
  const scaleContainer = labelNode.closest('div');
  if (!scaleContainer) throw new Error(`Could not find container for scale: ${String(scaleLabel)}`);
  await user.click(within(scaleContainer).getByRole('button', { name: String(score) }));
};

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
    
    expect(screen.getByText(/1\s+strongly disagree/i)).toBeInTheDocument();
    expect(screen.getByText(/5\s+strongly agree/i)).toBeInTheDocument();
  });

  it('allows selecting Likert scores and highlights selection', async () => {
    const user = userEvent.setup();
    render(
      <ClinicalConcordancePanel
        patientId="TEST_001"
        predictions={mockPredictions}
      />
    );

    await selectLikertScore(user, /diabetic retinopathy assessment/i, 4);
    const labelNode = screen.getByText(/diabetic retinopathy assessment/i);
    const scaleContainer = labelNode.closest('div');
    expect(within(scaleContainer as HTMLElement).getByRole('button', { name: '4' })).toHaveClass('bg-blue-500', 'bg-green-500', 'selected');
  });

  it('requires all three assessments before submission', async () => {
    const user = userEvent.setup();
    
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
    expect(submitBtn).toBeDisabled();
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
    const mockOnSubmit = vi.fn();
    render(
      <ClinicalConcordancePanel
        patientId="TEST_001"
        predictions={mockPredictions}
        onReviewSubmitted={mockOnSubmit}
      />
    );

    await selectLikertScore(user, /diabetic retinopathy assessment/i, 4);
    await selectLikertScore(user, /glaucoma screening assessment/i, 4);
    await selectLikertScore(user, /refraction accuracy assessment/i, 4);
    
    // Enter clinician ID
    const clinicianInput = screen.getByPlaceholderText(/clinician|expert/i);
    await user.type(clinicianInput, 'DR_001');
    
    // Submit
    const submitBtn = screen.getByRole('button', { name: /submit/i });
    await user.click(submitBtn);
    
    await waitFor(() => {
      expect(mockOnSubmit).toHaveBeenCalledWith(
        expect.objectContaining({
          dr_assessment: 4,
          glaucoma_assessment: 4,
          refraction_assessment: 4,
          clinician_id: 'DR_001',
        })
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
    await selectLikertScore(user, /diabetic retinopathy assessment/i, 4);
    await selectLikertScore(user, /glaucoma screening assessment/i, 4);
    await selectLikertScore(user, /refraction accuracy assessment/i, 4);
    
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
    expect(screen.getByText(/mild/i)).toBeInTheDocument();
    expect(screen.getByText(/normal/i)).toBeInTheDocument();
    expect(screen.getByText(/-0\.50/)).toBeInTheDocument();
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
    
    await selectLikertScore(user, /diabetic retinopathy assessment/i, 4);
    await selectLikertScore(user, /glaucoma screening assessment/i, 4);
    await selectLikertScore(user, /refraction accuracy assessment/i, 4);
    
    const clinicianInput = screen.getByPlaceholderText(/clinician/i);
    await user.type(clinicianInput, 'DR_001');
    
    const submitBtn = screen.getByRole('button', { name: /submit/i });
    await user.click(submitBtn);
    
    await waitFor(() => {
      expect(screen.getByText(/database error/i)).toBeInTheDocument();
    });
  });
});
