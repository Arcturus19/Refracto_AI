import React, { useState } from 'react';
import { Save, AlertCircle } from 'lucide-react';

interface ClinicalConcordanceReview {
  dr_assessment: number | null;      // 1-5 Likert scale
  glaucoma_assessment: number | null;
  refraction_assessment: number | null;
  clinician_notes?: string;
  clinician_id: string;
}

interface ClinicalConcordancePanelProps {
  patientId: string;
  predictions: {
    dr: string;
    glaucoma: string;
    refraction: { sphere: number; cylinder: number; axis: number };
  };
  onSubmitReview?: (review: ClinicalConcordanceReview) => Promise<void>;
  onReviewSubmitted?: (review: ClinicalConcordanceReview) => Promise<void>;
}

/**
 * Clinical Concordance Panel (Week 1 - P0.5)
 * 
 * Expert clinicians rate agreement with AI predictions using 1-5 Likert scales.
 * Directly enables H3 hypothesis validation: CCR ≥85% across expert panel.
 * 
 * Scales:
 * 1 = Strongly Disagree
 * 2 = Disagree
 * 3 = Neutral
 * 4 = Agree
 * 5 = Strongly Agree
 */
export const ClinicalConcordancePanel: React.FC<ClinicalConcordancePanelProps> = ({
  patientId,
  predictions,
  onSubmitReview,
  onReviewSubmitted,
}) => {
  const [review, setReview] = useState<ClinicalConcordanceReview>({
    dr_assessment: null,
    glaucoma_assessment: null,
    refraction_assessment: null,
    clinician_notes: '',
    clinician_id: localStorage.getItem('clinician_id') || ''
  });

  const [submitting, setSubmitting] = useState(false);
  const [submitted, setSubmitted] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);
  const [submitError, setSubmitError] = useState<string | null>(null);

  const handleScaleChange = (field: 'dr_assessment' | 'glaucoma_assessment' | 'refraction_assessment', value: number) => {
    setReview(prev => ({ ...prev, [field]: value }));
    setFormError(null);
  };

  const handleSubmit = async () => {
    if (!review.dr_assessment || !review.glaucoma_assessment || !review.refraction_assessment) {
      setFormError('Please rate all three assessments before submitting.');
      return;
    }

    if (!review.clinician_id) {
      setFormError('Please enter your clinician identifier.');
      return;
    }

    setSubmitting(true);
    setSubmitError(null);
    try {
      if (onReviewSubmitted) {
        await onReviewSubmitted(review);
      } else if (onSubmitReview) {
        await onSubmitReview(review);
      } else {
        // Default API call
        const response = await fetch('/api/ml/expert-review/submit', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            patient_id: patientId,
            ...review
          })
        });
        
        if (!response.ok) throw new Error('Submission failed');
        const data = await response.json();
        if (data.success === false) throw new Error(data.error || 'Submission failed');
      }
      setSubmitted(true);
      setTimeout(() => setSubmitted(false), 3000);
    } catch (err) {
      setSubmitError(err instanceof Error ? err.message : 'Failed to submit review');
    } finally {
      setSubmitting(false);
    }
  };

  const LikertScale = ({ value, onChange, label }: { value: number | null; onChange: (v: number) => void; label: string }) => {
    const scaleOptions = [
      { score: 1, label: 'Strongly Disagree', color: 'bg-red-500' },
      { score: 2, label: 'Disagree', color: 'bg-orange-500' },
      { score: 3, label: 'Neutral', color: 'bg-yellow-500' },
      { score: 4, label: 'Agree', color: 'bg-blue-500' },
      { score: 5, label: 'Strongly Agree', color: 'bg-green-500' }
    ];

    return (
      <div className="mb-6 p-4 bg-gray-50 rounded">
        <p className="text-sm font-semibold text-gray-700 mb-3">{label}</p>
        <div className="flex gap-1 justify-between">
          {scaleOptions.map(option => (
            <button
              key={option.score}
              onClick={() => onChange(option.score)}
              className={`flex-1 py-2 px-1 rounded font-bold transition ${
                value === option.score
                  ? `${option.color} bg-blue-500 bg-green-500 text-white selected`
                  : 'bg-white border-2 border-gray-300 hover:border-gray-400 text-gray-600'
              }`}
              title={option.label}
            >
              {option.score}
            </button>
          ))}
        </div>
        {value && (
          <p className="text-xs text-gray-500 mt-2">
            Selected: {scaleOptions.find(o => o.score === value)?.label}
          </p>
        )}
      </div>
    );
  };

  return (
    <div className="max-w-2xl mx-auto p-6 bg-white rounded-lg shadow">
      <h2 className="text-2xl font-bold mb-2 flex items-center gap-2">
        Expert Clinical Assessment
      </h2>
      <p className="text-sm text-gray-600 mb-6">
        Rate your agreement with the AI predictions (H3: Clinical Concordance Rate ≥85%)
      </p>

      {/* AI Predictions Summary */}
      <div className="mb-6 p-4 bg-blue-50 border border-blue-200 rounded">
        <h3 className="font-semibold text-blue-900 mb-3">AI Predictions to Review:</h3>
        <div className="space-y-2 text-sm">
          <p><span className="font-medium">Diabetic Retinopathy:</span> {predictions.dr}</p>
          <p><span className="font-medium">Glaucoma:</span> {predictions.glaucoma}</p>
          <p><span className="font-medium">Refraction:</span> {predictions.refraction.sphere > 0 ? '+' : ''}{predictions.refraction.sphere.toFixed(2)} / {predictions.refraction.cylinder > 0 ? '+' : ''}{predictions.refraction.cylinder.toFixed(2)} x {predictions.refraction.axis.toFixed(0)}°</p>
        </div>
      </div>

      {/* Scale Legend */}
      <div className="mb-4 flex justify-between text-xs text-gray-500">
        <span>1 Strongly Disagree</span>
        <span>2 Disagree</span>
        <span>3 Neutral</span>
        <span>4 Agree</span>
        <span>5 Strongly Agree</span>
      </div>

      {/* Likert Scales */}
      <div className="mb-6 space-y-4">
        <div className="text-sm font-semibold text-gray-700 mb-4">
          How much do you agree with each prediction?
        </div>

        <LikertScale
          label="Diabetic Retinopathy Assessment"
          value={review.dr_assessment}
          onChange={(v) => handleScaleChange('dr_assessment', v)}
        />

        <LikertScale
          label="Glaucoma Screening Assessment"
          value={review.glaucoma_assessment}
          onChange={(v) => handleScaleChange('glaucoma_assessment', v)}
        />

        <LikertScale
          label="Refraction Accuracy Assessment"
          value={review.refraction_assessment}
          onChange={(v) => handleScaleChange('refraction_assessment', v)}
        />
      </div>

      {/* Form Error */}
      {formError && (
        <div className="mb-4 p-3 bg-red-100 border border-red-300 rounded text-red-700" role="alert">
          {formError}
        </div>
      )}

      {/* Clinical Notes */}
      <div className="mb-6">
        <label className="block text-sm font-semibold text-gray-700 mb-2">
          Optional Clinical Notes
        </label>
        <textarea
          value={review.clinician_notes}
          onChange={(e) => setReview(prev => ({ ...prev, clinician_notes: e.target.value }))}
          placeholder="Add any relevant clinical observations or concerns..."
          rows={3}
          className="w-full p-3 border border-gray-300 rounded focus:outline-none focus:border-blue-500"
        />
      </div>

      {/* Clinician ID */}
      <div className="mb-6">
        <label className="block text-sm font-semibold text-gray-700 mb-2">
          Clinician ID *
        </label>
        <input
          type="text"
          value={review.clinician_id}
          onChange={(e) => setReview(prev => ({ ...prev, clinician_id: e.target.value }))}
          placeholder="Your clinician identifier (for audit trail)"
          className="w-full p-2 border border-gray-300 rounded focus:outline-none focus:border-blue-500"
        />
        <p className="text-xs text-gray-500 mt-1">Required for immutable audit logging</p>
      </div>

      {/* Information Box */}
      <div className="mb-6 p-4 bg-purple-50 border border-purple-200 rounded text-sm text-purple-800 flex items-start gap-2">
        <AlertCircle size={18} className="flex-shrink-0 mt-0.5" />
        <div>
          <p className="font-semibold">H3 Hypothesis Validation</p>
          <p>Your assessment contributes to validating: "Clinical Concordance Rate ≥85% achievable with AI support"</p>
          <p className="mt-1 text-xs">All submissions are logged immutably (P0.6 Audit Trail)</p>
        </div>
      </div>

      {/* Submit Error */}
      {submitError && (
        <div className="mb-4 p-3 bg-red-100 border border-red-300 rounded text-red-700" role="alert">
          {submitError}
        </div>
      )}

      {/* Submit Button */}
      {submitted && (
        <div className="mb-4 p-3 bg-green-100 border border-green-300 rounded text-green-700 flex items-center gap-2">
          <span>✓ Review submitted successfully. Thank you!</span>
        </div>
      )}

      <button
        onClick={handleSubmit}
        disabled={submitting || !review.dr_assessment || !review.glaucoma_assessment || !review.refraction_assessment}
        className="w-full bg-indigo-600 text-white py-3 rounded hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed font-medium transition flex items-center justify-center gap-2"
      >
        <Save size={18} />
        {submitting ? 'Submitting...' : 'Submit Expert Review'}
      </button>

      <p className="text-xs text-gray-500 text-center mt-4">
        This review will be aggregated with other expert assessments to calculate the global CCR.
      </p>
    </div>
  );
};
