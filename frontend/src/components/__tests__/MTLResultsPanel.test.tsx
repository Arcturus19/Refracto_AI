import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import { MTLResultsPanel } from '../MTLResultsPanel';
import { mockApiResponses, resetAllMocks } from '../../tests/setup';

describe('MTLResultsPanel Component', () => {
  beforeEach(() => {
    resetAllMocks();
  });

  it('displays all three prediction categories', () => {
    render(
      <MTLResultsPanel predictions={mockApiResponses.mtlAnalysis} />
    );
    
    expect(screen.getByText(/diabetic retinopathy/i)).toBeInTheDocument();
    expect(screen.getByText(/glaucoma/i)).toBeInTheDocument();
    expect(screen.getByText(/refraction/i)).toBeInTheDocument();
  });

  it('shows correct DR classification with confidence', () => {
    render(
      <MTLResultsPanel predictions={mockApiResponses.mtlAnalysis} />
    );
    
    expect(screen.getByText(/Mild/)).toBeInTheDocument();
    expect(screen.getByText(/0\.87|87%/)).toBeInTheDocument();
  });

  it('displays detailed class scores breakdown', () => {
    render(
      <MTLResultsPanel predictions={mockApiResponses.mtlAnalysis} />
    );
    
    expect(screen.getAllByText(/No DR|Mild|Moderate|Severe|Proliferative/)).toBeDefined();
  });

  it('shows glaucoma prediction with correction factor', () => {
    render(
      <MTLResultsPanel predictions={mockApiResponses.mtlAnalysis} />
    );
    
    expect(screen.getByText(/Normal/)).toBeInTheDocument();
    expect(screen.getByText(/1\.003|correction|myopia/i)).toBeInTheDocument();
  });

  it('displays refraction values correctly', () => {
    render(
      <MTLResultsPanel predictions={mockApiResponses.mtlAnalysis} />
    );
    
    expect(screen.getByText(/-0\.50|-0\.25|180/)).toBeInTheDocument();
  });

  it('shows confidence warning for low confidence predictions', () => {
    const lowConfidence = {
      ...mockApiResponses.mtlAnalysis,
      dr_prediction: {
        ...mockApiResponses.mtlAnalysis.dr_prediction,
        confidence: 0.65,
      },
    };
    
    render(<MTLResultsPanel predictions={lowConfidence} />);
    expect(screen.getByText(/low confidence|caution/i)).toBeInTheDocument();
  });

  it('renders confidence progress bars for all tasks', () => {
    render(
      <MTLResultsPanel predictions={mockApiResponses.mtlAnalysis} />
    );
    
    const progressBars = screen.getAllByRole('progressbar', { hidden: true });
    expect(progressBars.length).toBeGreaterThanOrEqual(3);
  });

  it('displays audit log ID for tracking', () => {
    render(
      <MTLResultsPanel predictions={mockApiResponses.mtlAnalysis} />
    );
    
    expect(screen.getByText(/LOG_TEST_001|audit.*log/i)).toBeInTheDocument();
  });

  it('shows timestamp of prediction', () => {
    render(
      <MTLResultsPanel predictions={mockApiResponses.mtlAnalysis} />
    );
    
    expect(screen.getByText(/timestamp|time|date/i)).toBeInTheDocument();
  });

  it('calls onRequestReview callback when button clicked', () => {
    const mockCallback = vi.fn();
    render(
      <MTLResultsPanel
        predictions={mockApiResponses.mtlAnalysis}
        onRequestReview={mockCallback}
      />
    );
    
    const reviewBtn = screen.getByRole('button', { name: /request.*review|expert review/i });
    reviewBtn.click();
    
    expect(mockCallback).toHaveBeenCalled();
  });

  it('displays all class scores in pie chart or breakdown', () => {
    render(
      <MTLResultsPanel predictions={mockApiResponses.mtlAnalysis} />
    );
    
    expect(screen.getByText(/0\.05|5%/)).toBeInTheDocument(); // No DR
    expect(screen.getByText(/0\.87|87%/)).toBeInTheDocument(); // Mild
    expect(screen.getByText(/0\.06|6%/)).toBeInTheDocument(); // Moderate
  });
});
