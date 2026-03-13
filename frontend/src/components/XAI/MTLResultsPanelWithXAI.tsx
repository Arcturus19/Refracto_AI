import React, { useState, useEffect } from 'react';
import { AlertCircle, Brain, ChevronDown, Loader } from 'lucide-react';
import {
  XAIModal,
  XAIInfoBanner,
  ExplanationPanel,
  ConfidenceBreakdown,
} from './ExplanationComponents';

interface MTLPredictionResult {
  prediction_id: string;
  dr_prediction: number;
  glaucoma_prediction: float;
  refraction_sphere: float;
  refraction_cylinder: float;
  refraction_axis: float;
  dr_confidence: float;
  glaucoma_confidence: float;
  refraction_confidence: float;
  dr_classes: Record<string, float>;
}

/**
 * Enhanced MTLResultsPanel with XAI Integration
 * Displays multi-task learning results with explainability
 */
export const MTLResultsPanelWithXAI: React.FC<{
  results: MTLPredictionResult;
  onRequestReview?: (predictionId: string) => void;
}> = ({ results, onRequestReview }) => {
  const [showXAIModal, setShowXAIModal] = useState(false);
  const [selectedTask, setSelectedTask] = useState<'dr' | 'glaucoma' | 'refraction'>('dr');
  const [explanations, setExplanations] = useState<Record<string, any>>({});
  const [loading, setLoading] = useState(false);
  const [expandedSections, setExpandedSections] = useState<Record<string, boolean>>({});

  // Fetch explanations when modal opens
  useEffect(() => {
    if (showXAIModal && !explanations[selectedTask]) {
      fetchExplanation();
    }
  }, [showXAIModal, selectedTask]);

  const fetchExplanation = async () => {
    setLoading(true);
    try {
      let endpoint = '';
      let payload = {
        prediction_id: results.prediction_id,
        confidence: 0,
        class_probabilities: undefined,
      };

      if (selectedTask === 'dr') {
        endpoint = '/api/ml/xai/explain/dr';
        payload = {
          ...payload,
          dr_prediction: results.dr_prediction,
          confidence: results.dr_confidence,
          class_probabilities: results.dr_classes,
        };
      } else if (selectedTask === 'glaucoma') {
        endpoint = '/api/ml/xai/explain/glaucoma';
        payload = {
          ...payload,
          glaucoma_score: results.glaucoma_prediction,
          confidence: results.glaucoma_confidence,
        };
      } else {
        endpoint = '/api/ml/xai/explain/refraction';
        payload = {
          ...payload,
          sphere: results.refraction_sphere,
          cylinder: results.refraction_cylinder,
          axis: results.refraction_axis,
          confidence: results.refraction_confidence,
        };
      }

      const response = await fetch(endpoint, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
        },
        body: JSON.stringify(payload),
      });

      if (!response.ok) throw new Error('Failed to fetch explanation');

      const explanation = await response.json();
      setExplanations(prev => ({
        ...prev,
        [selectedTask]: explanation,
      }));
    } catch (error) {
      console.error('Error fetching explanation:', error);
    } finally {
      setLoading(false);
    }
  };

  const toggleSection = (section: string) => {
    setExpandedSections(prev => ({
      ...prev,
      [section]: !prev[section],
    }));
  };

  const getDRSeverityLabel = (prediction: number): string => {
    const labels = [
      'No Diabetic Retinopathy',
      'Mild',
      'Moderate',
      'Severe',
      'Proliferative'
    ];
    return labels[prediction] || 'Unknown';
  };

  const getConfidenceColor = (confidence: number): string => {
    if (confidence >= 0.85) return 'text-green-600 bg-green-50';
    if (confidence >= 0.70) return 'text-yellow-600 bg-yellow-50';
    return 'text-red-600 bg-red-50';
  };

  const getConfidenceBG = (confidence: number): string => {
    if (confidence >= 0.85) return 'bg-green-500';
    if (confidence >= 0.70) return 'bg-yellow-500';
    return 'bg-red-500';
  };

  return (
    <div className="space-y-4 w-full">
      {/* Header */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Brain className="w-5 h-5" />
            Multi-Task Learning Results
          </CardTitle>
          <CardDescription>
            AI predictions with explainability analysis
          </CardDescription>
        </CardHeader>
      </Card>

      {/* DR Results */}
      <Card>
        <CardHeader
          onClick={() => toggleSection('dr')}
          className="cursor-pointer hover:bg-gray-50"
        >
          <div className="flex items-center justify-between">
            <CardTitle className="text-lg">Diabetic Retinopathy (DR)</CardTitle>
            <ChevronDown
              className={`w-5 h-5 transition-transform ${
                expandedSections['dr'] ? 'transform rotate-180' : ''
              }`}
            />
          </div>
        </CardHeader>

        {expandedSections['dr'] && (
          <CardContent className="space-y-4">
            {/* Prediction Display */}
            <div className="grid grid-cols-2 gap-4">
              <div className="p-4 bg-blue-50 rounded-lg border border-blue-200">
                <div className="text-sm text-gray-600 mb-1">Severity</div>
                <div className="text-2xl font-bold text-blue-700">
                  {getDRSeverityLabel(results.dr_prediction)}
                </div>
                <div className="text-xs text-gray-500 mt-2">Class {results.dr_prediction}</div>
              </div>

              <div className={`p-4 rounded-lg border ${getConfidenceColor(results.dr_confidence)}`}>
                <div className="text-sm text-gray-600 mb-1">Confidence</div>
                <div className="text-2xl font-bold">
                  {(results.dr_confidence * 100).toFixed(1)}%
                </div>
                <div className="w-full h-2 bg-gray-200 rounded-full mt-2 overflow-hidden">
                  <div
                    className={`h-full ${getConfidenceBG(results.dr_confidence)}`}
                    style={{ width: `${results.dr_confidence * 100}%` }}
                  />
                </div>
              </div>
            </div>

            {/* Class Scores */}
            <div className="space-y-2">
              <h4 className="font-semibold text-sm text-gray-700">Class Breakdown</h4>
              {Object.entries(results.dr_classes || {}).map(([className, score]) => (
                <div key={className} className="space-y-1">
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-600">{className}</span>
                    <span className="font-medium">{(score * 100).toFixed(1)}%</span>
                  </div>
                  <div className="w-full h-2 bg-gray-200 rounded-full overflow-hidden">
                    <div
                      className="h-full bg-blue-500 rounded-full"
                      style={{ width: `${score * 100}%` }}
                    />
                  </div>
                </div>
              ))}
            </div>

            {/* XAI Section */}
            <div className="border-t pt-4">
              {explanations['dr'] ? (
                <div className="space-y-3">
                  <XAIInfoBanner
                    explanation={explanations['dr']}
                    onExplore={() => {
                      setSelectedTask('dr');
                      setShowXAIModal(true);
                    }}
                  />
                </div>
              ) : (
                <button
                  onClick={() => {
                    setSelectedTask('dr');
                    setShowXAIModal(true);
                  }}
                  className="w-full px-4 py-3 text-left bg-gradient-to-r from-indigo-50 to-blue-50 border border-indigo-200 rounded-lg hover:border-indigo-300 transition-colors"
                >
                  <div className="flex items-center gap-2 text-indigo-700 font-medium">
                    <Brain className="w-4 h-4" />
                    View AI Explanation
                  </div>
                  <p className="text-xs text-indigo-600 mt-1">
                    Understand why the model made this prediction
                  </p>
                </button>
              )}
            </div>

            {/* Low Confidence Warning */}
            {results.dr_confidence < 0.70 && (
              <div className="p-3 bg-yellow-50 border border-yellow-200 rounded-lg flex gap-2">
                <AlertCircle className="w-5 h-5 text-yellow-600 flex-shrink-0 mt-0.5" />
                <div className="text-sm text-yellow-800">
                  <strong>Low Confidence Warning:</strong> Model confidence is below 70%. Recommend expert review.
                </div>
              </div>
            )}
          </CardContent>
        )}
      </Card>

      {/* Glaucoma Results */}
      <Card>
        <CardHeader
          onClick={() => toggleSection('glaucoma')}
          className="cursor-pointer hover:bg-gray-50"
        >
          <div className="flex items-center justify-between">
            <CardTitle className="text-lg">Glaucoma Risk Assessment</CardTitle>
            <ChevronDown
              className={`w-5 h-5 transition-transform ${
                expandedSections['glaucoma'] ? 'transform rotate-180' : ''
              }`}
            />
          </div>
        </CardHeader>

        {expandedSections['glaucoma'] && (
          <CardContent className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div className="p-4 bg-purple-50 rounded-lg border border-purple-200">
                <div className="text-sm text-gray-600 mb-1">Risk Score</div>
                <div className="text-2xl font-bold text-purple-700">
                  {(results.glaucoma_prediction * 100).toFixed(1)}
                </div>
                <div className="text-xs text-gray-500 mt-2">
                  {results.glaucoma_prediction > 0.7 ? 'High Risk' : results.glaucoma_prediction > 0.5 ? 'Moderate Risk' : 'Low Risk'}
                </div>
              </div>

              <div className={`p-4 rounded-lg border ${getConfidenceColor(results.glaucoma_confidence)}`}>
                <div className="text-sm text-gray-600 mb-1">Confidence</div>
                <div className="text-2xl font-bold">
                  {(results.glaucoma_confidence * 100).toFixed(1)}%
                </div>
                <div className="w-full h-2 bg-gray-200 rounded-full mt-2 overflow-hidden">
                  <div
                    className={`h-full ${getConfidenceBG(results.glaucoma_confidence)}`}
                    style={{ width: `${results.glaucoma_confidence * 100}%` }}
                  />
                </div>
              </div>
            </div>

            {/* XAI Section */}
            <div className="border-t pt-4">
              <button
                onClick={() => {
                  setSelectedTask('glaucoma');
                  setShowXAIModal(true);
                }}
                className="w-full px-4 py-3 text-left bg-gradient-to-r from-purple-50 to-pink-50 border border-purple-200 rounded-lg hover:border-purple-300 transition-colors"
              >
                <div className="flex items-center gap-2 text-purple-700 font-medium">
                  <Brain className="w-4 h-4" />
                  View AI Explanation
                </div>
              </button>
            </div>
          </CardContent>
        )}
      </Card>

      {/* Refraction Results */}
      <Card>
        <CardHeader
          onClick={() => toggleSection('refraction')}
          className="cursor-pointer hover:bg-gray-50"
        >
          <div className="flex items-center justify-between">
            <CardTitle className="text-lg">Refraction Estimate</CardTitle>
            <ChevronDown
              className={`w-5 h-5 transition-transform ${
                expandedSections['refraction'] ? 'transform rotate-180' : ''
              }`}
            />
          </div>
        </CardHeader>

        {expandedSections['refraction'] && (
          <CardContent className="space-y-4">
            <div className="grid grid-cols-3 gap-3">
              <div className="p-4 bg-emerald-50 rounded-lg border border-emerald-200">
                <div className="text-xs text-gray-600 mb-1">Sphere</div>
                <div className="text-2xl font-bold text-emerald-700">
                  {results.refraction_sphere > 0 ? '+' : ''}{results.refraction_sphere.toFixed(2)}
                </div>
                <div className="text-xs text-gray-500 mt-1">Diopters</div>
              </div>

              <div className="p-4 bg-cyan-50 rounded-lg border border-cyan-200">
                <div className="text-xs text-gray-600 mb-1">Cylinder</div>
                <div className="text-2xl font-bold text-cyan-700">
                  {results.refraction_cylinder > 0 ? '+' : ''}{results.refraction_cylinder.toFixed(2)}
                </div>
                <div className="text-xs text-gray-500 mt-1">Diopters</div>
              </div>

              <div className="p-4 bg-orange-50 rounded-lg border border-orange-200">
                <div className="text-xs text-gray-600 mb-1">Axis</div>
                <div className="text-2xl font-bold text-orange-700">
                  {results.refraction_axis.toFixed(0)}°
                </div>
                <div className="text-xs text-gray-500 mt-1">Degrees</div>
              </div>
            </div>

            <div className={`p-4 rounded-lg border ${getConfidenceColor(results.refraction_confidence)}`}>
              <div className="flex justify-between items-center mb-2">
                <span className="text-sm text-gray-600">Prediction Confidence</span>
                <span className="font-bold">{(results.refraction_confidence * 100).toFixed(1)}%</span>
              </div>
              <div className="w-full h-2 bg-gray-200 rounded-full overflow-hidden">
                <div
                  className={`h-full ${getConfidenceBG(results.refraction_confidence)}`}
                  style={{ width: `${results.refraction_confidence * 100}%` }}
                />
              </div>
            </div>

            {/* XAI Section */}
            <div className="border-t pt-4">
              <button
                onClick={() => {
                  setSelectedTask('refraction');
                  setShowXAIModal(true);
                }}
                className="w-full px-4 py-3 text-left bg-gradient-to-r from-emerald-50 to-cyan-50 border border-emerald-200 rounded-lg hover:border-emerald-300 transition-colors"
              >
                <div className="flex items-center gap-2 text-emerald-700 font-medium">
                  <Brain className="w-4 h-4" />
                  View AI Explanation
                </div>
              </button>
            </div>
          </CardContent>
        )}
      </Card>

      {/* Actions */}
      <Card>
        <CardContent className="pt-6">
          <button
            onClick={() => onRequestReview?.(results.prediction_id)}
            className="w-full px-4 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 font-medium transition-colors"
          >
            Request Expert Review
          </button>
        </CardContent>
      </Card>

      {/* XAI Modal */}
      <XAIModal
        isOpen={showXAIModal}
        onClose={() => setShowXAIModal(false)}
        explanation={explanations[selectedTask]}
        attendionMapData={explanations[selectedTask]?.attention_map}
      />
    </div>
  );
};

export default MTLResultsPanelWithXAI;
