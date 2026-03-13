import React from 'react';
import { AlertCircle, CheckCircle, TrendingUp } from 'lucide-react';

interface MTLPredictions {
  diabetic_retinopathy: {
    class: 'No DR' | 'Mild' | 'Moderate' | 'Severe' | 'Proliferative';
    confidence: number;
    class_scores: Record<string, number>;
  };
  glaucoma: {
    prediction: 'Normal' | 'Glaucoma';
    confidence: number;
    original_logit: number;
    corrected_logit: number;
    correction_factor: number;
  };
  refraction: {
    sphere: number;
    cylinder: number;
    axis: number;
    confidence: number;
  };
  model_version: string;
  timestamp: string;
  patient_id: string;
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
  const drRiskColor = {
    'No DR': 'bg-green-100 text-green-800 border-green-300',
    'Mild': 'bg-yellow-100 text-yellow-800 border-yellow-300',
    'Moderate': 'bg-orange-100 text-orange-800 border-orange-300',
    'Severe': 'bg-red-100 text-red-800 border-red-300',
    'Proliferative': 'bg-red-200 text-red-900 border-red-400'
  };

  const glaucomaRiskColor = predictions.glaucoma.prediction === 'Normal'
    ? 'bg-green-100 text-green-800 border-green-300'
    : 'bg-red-100 text-red-800 border-red-300';

  const confidenceBar = (conf: number) => (
    <div className="w-full bg-gray-300 rounded-full h-2">
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
          <p>Model: {predictions.model_version}</p>
          <p>{new Date(predictions.timestamp).toLocaleString()}</p>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {/* Diabetic Retinopathy */}
        <div className={`p-4 rounded-lg border-2 ${drRiskColor[predictions.diabetic_retinopathy.class]}`}>
          <h3 className="font-bold mb-2">Diabetic Retinopathy</h3>
          <p className="text-2xl font-bold mb-3">{predictions.diabetic_retinopathy.class}</p>
          <div className="space-y-2 mb-3">
            <div className="flex justify-between text-sm">
              <span>Confidence</span>
              <span>{(predictions.diabetic_retinopathy.confidence * 100).toFixed(1)}%</span>
            </div>
            {confidenceBar(predictions.diabetic_retinopathy.confidence)}
          </div>
          <details className="text-sm">
            <summary className="cursor-pointer text-gray-600 hover:text-gray-800">Class scores</summary>
            <div className="mt-2 space-y-1 text-xs">
              {Object.entries(predictions.diabetic_retinopathy.class_scores).map(([cls, score]) => (
                <div key={cls} className="flex justify-between">
                  <span>{cls}</span>
                  <span className="font-mono">{(score * 100).toFixed(1)}%</span>
                </div>
              ))}
            </div>
          </details>
        </div>

        {/* Glaucoma (with correction indicator) */}
        <div className={`p-4 rounded-lg border-2 ${glaucomaRiskColor} relative`}>
          <h3 className="font-bold mb-2">Glaucoma Screening</h3>
          <p className="text-2xl font-bold mb-3">{predictions.glaucoma.prediction}</p>
          <div className="space-y-2 mb-3">
            <div className="flex justify-between text-sm">
              <span>Confidence</span>
              <span>{(predictions.glaucoma.confidence * 100).toFixed(1)}%</span>
            </div>
            {confidenceBar(predictions.glaucoma.confidence)}
          </div>

          {/* Myopia Correction Indicator */}
          {Math.abs(predictions.glaucoma.correction_factor - 1.0) > 0.05 && (
            <div className="mt-3 p-2 bg-blue-50 border border-blue-200 rounded text-xs">
              <div className="flex items-start gap-2">
                <TrendingUp size={14} className="text-blue-600 mt-0.5 flex-shrink-0" />
                <div>
                  <p className="font-semibold text-blue-900">Myopia Correction Applied</p>
                  <p className="text-blue-700">
                    Factor: {predictions.glaucoma.correction_factor.toFixed(2)}x
                  </p>
                  <p className="text-blue-600 text-xs mt-1">
                    Original: {predictions.glaucoma.original_logit.toFixed(2)} → 
                    Corrected: {predictions.glaucoma.corrected_logit.toFixed(2)}
                  </p>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Refraction */}
        <div className="p-4 rounded-lg border-2 bg-purple-100 text-purple-800 border-purple-300">
          <h3 className="font-bold mb-3">Predicted Refraction</h3>
          <div className="space-y-2 mb-3 font-mono">
            <div className="flex justify-between">
              <span className="font-normal">Sphere (SPH):</span>
              <span className="font-bold">{predictions.refraction.sphere > 0 ? '+' : ''}{predictions.refraction.sphere.toFixed(2)} D</span>
            </div>
            <div className="flex justify-between">
              <span className="font-normal">Cylinder (CYL):</span>
              <span className="font-bold">{predictions.refraction.cylinder > 0 ? '+' : ''}{predictions.refraction.cylinder.toFixed(2)} D</span>
            </div>
            <div className="flex justify-between">
              <span className="font-normal">Axis (AX):</span>
              <span className="font-bold">{predictions.refraction.axis.toFixed(0)}°</span>
            </div>
          </div>
          <div className="space-y-1">
            <div className="flex justify-between text-sm">
              <span>Confidence</span>
              <span>{(predictions.refraction.confidence * 100).toFixed(1)}%</span>
            </div>
            {confidenceBar(predictions.refraction.confidence)}
          </div>
        </div>
      </div>

      {/* Warnings */}
      {predictions.diabetic_retinopathy.confidence < 0.7 && (
        <div className="p-3 bg-yellow-100 border border-yellow-300 rounded flex items-start gap-2 text-yellow-800">
          <AlertCircle size={18} className="flex-shrink-0 mt-0.5" />
          <div>
            <p className="font-semibold">Low Confidence (DR)</p>
            <p className="text-sm">Consider image quality review or manual assessment</p>
          </div>
        </div>
      )}

      {predictions.glaucoma.confidence < 0.7 && (
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
        For research purposes, results are logged immutably for audit trail (H3 hypothesis: CCR ≥85%).
      </p>
    </div>
  );
};
