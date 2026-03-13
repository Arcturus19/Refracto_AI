import React from 'react';
import { AlertCircle, CheckCircle, TrendingUp } from 'lucide-react';

interface MTLPredictions {
  dr_prediction: {
    class: string;
    confidence: number;
    class_scores: Record<string, number>;
  };
  glaucoma_prediction: {
    prediction: string;
    confidence: number;
    original_logit: number;
    corrected_logit: number;
    correction_factor: number;
  };
  refraction_prediction: {
    sphere: number;
    cylinder: number;
    axis: number;
    confidence: number;
  };
  model_version?: string;
  timestamp: string;
  patient_id?: string;
  audit_log_id?: string;
  correction_factor?: number;
}

interface MTLResultsPanelProps {
  predictions: MTLPredictions;
  onRequestReview?: () => void;
}

/**
 * MTL Results Panel (Week 1 - P0.1/P0.2)
 *
 * Displays all three simultaneous predictions:
 * - Diabetic Retinopathy (5-class)
 * - Glaucoma (2-class, with myopia correction applied)
 * - Refraction (sphere, cylinder, axis)
 *
 * Shows correction factor from refracto-pathological link (P0.2)
 */
export const MTLResultsPanel: React.FC<MTLResultsPanelProps> = ({ predictions, onRequestReview }) => {
  const drRiskColor: Record<string, string> = {
    'No DR': 'bg-green-100 text-green-800 border-green-300',
    'Mild': 'bg-yellow-100 text-yellow-800 border-yellow-300',
    'Moderate': 'bg-orange-100 text-orange-800 border-orange-300',
    'Severe': 'bg-red-100 text-red-800 border-red-300',
    'Proliferative': 'bg-red-200 text-red-900 border-red-400',
  };

  const drColor = drRiskColor[predictions.dr_prediction.class] ?? 'bg-gray-100 text-gray-800 border-gray-300';

  const glaucomaRiskColor = predictions.glaucoma_prediction.prediction === 'Normal'
    ? 'bg-green-100 text-green-800 border-green-300'
    : 'bg-red-100 text-red-800 border-red-300';

  const confidenceBar = (conf: number) => (
    <div
      role="progressbar"
      aria-valuenow={Math.round(conf * 100)}
      aria-valuemin={0}
      aria-valuemax={100}
      className="w-full bg-gray-300 rounded-full h-2"
    >
      <div
        className="bg-blue-600 h-2 rounded-full transition-all"
        style={{ width: `${conf * 100}%` }}
      />
    </div>
  );

  return (
    <div className="max-w-5xl mx-auto p-6 bg-white rounded-lg shadow space-y-6">
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-2xl font-bold flex items-center gap-2">
          <CheckCircle className="text-green-600" />
          Multi-Task Learning Results
        </h2>
        <div className="text-sm text-gray-500">
          {predictions.model_version && <p>Model: {predictions.model_version}</p>}
          <p>Timestamp: {new Date(predictions.timestamp).toLocaleString()}</p>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {/* Diabetic Retinopathy */}
        <div className={`p-4 rounded-lg border-2 ${drColor}`}>
          <h3 className="font-bold mb-2">Diabetic Retinopathy</h3>
          <p className="text-2xl font-bold mb-3">{predictions.dr_prediction.class}</p>
          <div className="space-y-2 mb-3">
            <div className="flex justify-between text-sm">
              <span>Confidence</span>
              <span>{(predictions.dr_prediction.confidence * 100).toFixed(1)}%</span>
            </div>
            {confidenceBar(predictions.dr_prediction.confidence)}
          </div>
          <div className="text-sm mt-3">
            <p className="text-xs font-semibold text-gray-600 mb-1">Class Scores</p>
            <div className="space-y-1 text-xs">
              {Object.entries(predictions.dr_prediction.class_scores).map(([cls, score]) => (
                <div key={cls} className="flex justify-between">
                  <abbr title={cls} aria-label={cls} className="text-gray-500">{cls.substring(0, 3)}</abbr>
                  <span className="font-mono">{(score as number).toFixed(2)}</span>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Glaucoma (with correction indicator) */}
        <div className={`p-4 rounded-lg border-2 ${glaucomaRiskColor} relative`}>
          <h3 className="font-bold mb-2">Glaucoma Screening</h3>
          <p className="text-2xl font-bold mb-3">{predictions.glaucoma_prediction.prediction}</p>
          <div className="space-y-2 mb-3">
            <div className="flex justify-between text-sm">
              <span>Confidence</span>
              <span>{(predictions.glaucoma_prediction.confidence * 100).toFixed(1)}%</span>
            </div>
            {confidenceBar(predictions.glaucoma_prediction.confidence)}
          </div>

          {/* Myopia Correction — always shown */}
          <div className="mt-3 p-2 bg-blue-50 border border-blue-200 rounded text-xs">
            <div className="flex items-start gap-2">
              <TrendingUp size={14} className="text-blue-600 mt-0.5 flex-shrink-0" />
              <p className="text-blue-800">
                Myopia correction: {predictions.glaucoma_prediction.correction_factor.toFixed(3)} (
                {predictions.glaucoma_prediction.original_logit.toFixed(3)} →{' '}
                {predictions.glaucoma_prediction.corrected_logit.toFixed(3)})
              </p>
            </div>
          </div>
        </div>

        {/* Refraction */}
        <div className="p-4 rounded-lg border-2 bg-purple-100 text-purple-800 border-purple-300">
          <h3 className="font-bold mb-3">Predicted Refraction</h3>
          <div className="space-y-2 mb-3 font-mono">
            <p>
              SPH: {predictions.refraction_prediction.sphere > 0 ? '+' : ''}{predictions.refraction_prediction.sphere.toFixed(2)} D
              {' / '}CYL: {predictions.refraction_prediction.cylinder > 0 ? '+' : ''}{predictions.refraction_prediction.cylinder.toFixed(2)} D
              {' × '}{predictions.refraction_prediction.axis.toFixed(0)}°
            </p>
          </div>
          <div className="space-y-1">
            <div className="flex justify-between text-sm">
              <span>Confidence</span>
              <span>{(predictions.refraction_prediction.confidence * 100).toFixed(1)}%</span>
            </div>
            {confidenceBar(predictions.refraction_prediction.confidence)}
          </div>
        </div>
      </div>

      {/* Warnings */}
      {predictions.dr_prediction.confidence < 0.7 && (
        <div className="p-3 bg-yellow-100 border border-yellow-300 rounded flex items-start gap-2 text-yellow-800">
          <AlertCircle size={18} className="flex-shrink-0 mt-0.5" />
          <div>
            <p className="font-semibold">Low Confidence (DR)</p>
            <p className="text-sm">Consider image quality review or manual assessment</p>
          </div>
        </div>
      )}

      {predictions.glaucoma_prediction.confidence < 0.7 && (
        <div className="p-3 bg-yellow-100 border border-yellow-300 rounded flex items-start gap-2 text-yellow-800">
          <AlertCircle size={18} className="flex-shrink-0 mt-0.5" />
          <div>
            <p className="font-semibold">Low Confidence (Glaucoma)</p>
            <p className="text-sm">Consider additional clinical assessment</p>
          </div>
        </div>
      )}

      {/* Clinical Review Request */}
      <button
        onClick={onRequestReview}
        className="w-full bg-indigo-600 text-white py-2 rounded hover:bg-indigo-700 font-medium transition flex items-center justify-center gap-2"
      >
        <AlertCircle size={18} />
        Request Expert Review (CCR Validation)
      </button>

      {/* Footer note */}
      <p className="text-xs text-gray-500 border-t pt-4">
        This is an AI-assisted analysis. All results should be reviewed by qualified clinicians.
      </p>
      {predictions.audit_log_id && (
        <p className="text-xs text-gray-500 font-mono">Audit Log: {predictions.audit_log_id}</p>
      )}
    </div>
  );
};
