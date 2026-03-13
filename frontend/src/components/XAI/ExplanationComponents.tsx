import React, { useState, useEffect } from 'react';
import { AlertCircle, Brain, TrendingUp, Eye, ChevronDown } from 'lucide-react';

// Minimal Card UI primitives
export const Card: React.FC<{ children: React.ReactNode; className?: string }> = ({ children, className = '' }) => (
  <div className={`bg-white border border-gray-200 rounded-lg shadow-sm ${className}`}>{children}</div>
);
export const CardHeader: React.FC<{ children: React.ReactNode; className?: string; onClick?: () => void; style?: React.CSSProperties }> = ({ children, className = '', onClick, style }) => (
  <div className={`px-4 py-3 border-b border-gray-100 ${className}`} onClick={onClick} style={style}>{children}</div>
);
export const CardTitle: React.FC<{ children: React.ReactNode; className?: string }> = ({ children, className = '' }) => (
  <h3 className={`font-semibold text-gray-900 ${className}`}>{children}</h3>
);
export const CardDescription: React.FC<{ children: React.ReactNode; className?: string }> = ({ children, className = '' }) => (
  <p className={`text-sm text-gray-500 ${className}`}>{children}</p>
);
export const CardContent: React.FC<{ children: React.ReactNode; className?: string }> = ({ children, className = '' }) => (
  <div className={`px-4 py-3 ${className}`}>{children}</div>
);

// Minimal Tabs UI primitives
export const Tabs: React.FC<{ children: React.ReactNode; defaultValue?: string; className?: string }> = ({ children, className = '' }) => (
  <div className={className}>{children}</div>
);
export const TabsList: React.FC<{ children: React.ReactNode; className?: string }> = ({ children, className = '' }) => (
  <div className={`flex border-b border-gray-200 ${className}`}>{children}</div>
);
export const TabsTrigger: React.FC<{ children: React.ReactNode; value: string; className?: string }> = ({ children, className = '' }) => (
  <button className={`px-4 py-2 text-sm font-medium ${className}`}>{children}</button>
);
export const TabsContent: React.FC<{ children: React.ReactNode; value: string; className?: string }> = ({ children, className = '' }) => (
  <div className={className}>{children}</div>
);

interface ExplanationData {
  prediction_id: string;
  task: string;
  prediction_value: any;
  confidence: number;
  explanation_text: string;
  reasoning_steps: string[];
  confidence_level: 'high' | 'medium' | 'low';
  prediction_uncertainty: number;
  feature_importance?: Record<string, number>;
  top_contributing_features?: Array<{ feature: string; importance: number }>;
  class_probabilities?: Record<string, number>;
  confidence_sources?: Record<string, number>;
  timestamp: string;
}

/**
 * ExplanationPanel Component
 * Displays text-based explanation and reasoning steps
 */
export const ExplanationPanel: React.FC<{ explanation: ExplanationData }> = ({
  explanation,
}) => {
  const getConfidenceColor = (level: string) => {
    switch (level) {
      case 'high':
        return 'text-green-600 bg-green-50';
      case 'medium':
        return 'text-yellow-600 bg-yellow-50';
      case 'low':
        return 'text-red-600 bg-red-50';
      default:
        return 'text-gray-600 bg-gray-50';
    }
  };

  const getConfidenceBadgeText = (level: string) => {
    return level.charAt(0).toUpperCase() + level.slice(1);
  };

  return (
    <div className="w-full border rounded-lg shadow-sm bg-white">
      <div className="p-6 border-b">
        <div className="flex items-center gap-2 mb-2">
          <Brain className="w-5 h-5" />
          <h3 className="text-lg font-semibold">AI Explanation</h3>
        </div>
        <p className="text-sm text-gray-600">
          Model interpretation for {explanation.task} prediction
        </p>
      </div>
      <div className="p-6 space-y-6">
        {/* Main Explanation */}
        <div className="space-y-3">
          <div
            className={`p-4 rounded-lg border ${getConfidenceColor(
              explanation.confidence_level
            )} border-current`}
          >
            <div className="flex items-start gap-3">
              {explanation.confidence_level === 'low' && (
                <AlertCircle className="w-5 h-5 mt-0.5 flex-shrink-0" />
              )}
              <div>
                <p className="font-medium">{explanation.explanation_text}</p>
              </div>
            </div>
          </div>

          {/* Confidence Badge */}
          <div className="flex items-center gap-4">
            <span className="text-sm font-medium text-gray-600">
              Confidence Level:
            </span>
            <span
              className={`px-3 py-1 rounded-full text-sm font-semibold ${getConfidenceColor(
                explanation.confidence_level
              )}`}
            >
              {getConfidenceBadgeText(explanation.confidence_level)} (
              {(explanation.confidence * 100).toFixed(1)}%)
            </span>
          </div>
        </div>

        {/* Reasoning Steps */}
        <div className="space-y-3">
          <h3 className="font-semibold text-sm text-gray-700">
            Reasoning Steps:
          </h3>
          <div className="space-y-2">
            {explanation.reasoning_steps?.map((step, index) => (
              <div
                key={index}
                className="flex gap-3 text-sm p-2 rounded bg-gray-50"
              >
                <span className="inline-flex items-center justify-center w-6 h-6 rounded-full bg-blue-100 text-blue-700 font-semibold flex-shrink-0">
                  {index + 1}
                </span>
                <span className="text-gray-700 pt-0.5">{step}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Class Probabilities */}
        {explanation.class_probabilities && (
          <div className="space-y-3">
            <h3 className="font-semibold text-sm text-gray-700">
              Class Probabilities:
            </h3>
            <div className="space-y-2">
              {Object.entries(explanation.class_probabilities)
                .sort(([, a], [, b]) => b - a)
                .map(([className, probability]) => (
                  <div key={className} className="space-y-1">
                    <div className="flex justify-between text-sm">
                      <span className="text-gray-600">{className}</span>
                      <span className="font-medium text-gray-700">
                        {(probability * 100).toFixed(1)}%
                      </span>
                    </div>
                    <div className="w-full h-2 bg-gray-200 rounded-full overflow-hidden">
                      <div
                        className="h-full bg-blue-500 rounded-full transition-all"
                        style={{ width: `${probability * 100}%` }}
                      />
                    </div>
                  </div>
                ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

/**
 * AttentionMapViewer Component
 * Displays visual attention maps (Grad-CAM/saliency)
 */
export const AttentionMapViewer: React.FC<{
  mapData?: string;
  mapType: 'attention' | 'saliency';
}> = ({ mapData, mapType }) => {
  return (
    <div className="w-full border rounded-lg shadow-sm bg-white">
      <div className="p-6 border-b">
        <div className="flex items-center gap-2 mb-2">
          <Eye className="w-5 h-5" />
          <h3 className="text-lg font-semibold">{mapType === 'attention' ? 'Attention Map' : 'Saliency Map'}</h3>
        </div>
        <p className="text-sm text-gray-600">
          {mapType === 'attention'
            ? 'Regions that influenced the prediction (red = high influence)'
            : 'Pixel-level importance for the prediction'}
        </p>
      </div>
      <div className="p-6">
        {mapData ? (
          <div className="bg-gray-100 rounded-lg p-4 flex items-center justify-center min-h-64">
            <div className="text-center text-gray-600">
              <Eye className="w-12 h-12 mx-auto mb-2 opacity-50" />
              <p className="text-sm">Visual map would be displayed here</p>
              <p className="text-xs text-gray-500 mt-1">
                Base64 encoded image data: {mapData.substring(0, 50)}...
              </p>
            </div>
          </div>
        ) : (
          <div className="bg-gray-50 rounded-lg p-8 flex items-center justify-center text-gray-500">
            No map data available
          </div>
        )}
      </div>
    </div>
  );
};

/**
 * FeatureImportanceChart Component
 * Displays feature importance scores
 */
export const FeatureImportanceChart: React.FC<{
  features?: Array<{ feature: string; importance: number }>;
}> = ({ features = [] }) => {
  return (
    <Card className="w-full">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <TrendingUp className="w-5 h-5" />
          Feature Importance
        </CardTitle>
        <CardDescription>
          Contributing factors to this prediction
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        {features.length > 0 ? (
          <div className="space-y-4">
            {features.map((item, index) => (
              <div key={index} className="space-y-2">
                <div className="flex justify-between text-sm">
                  <span className="font-medium text-gray-700">
                    {item.feature.replace(/_/g, ' ')}
                  </span>
                  <span className="text-gray-600">
                    {(item.importance * 100).toFixed(1)}%
                  </span>
                </div>
                <div className="w-full h-3 bg-gray-200 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-gradient-to-r from-blue-500 to-blue-600 rounded-full transition-all"
                    style={{ width: `${item.importance * 100}%` }}
                  />
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="text-center py-6 text-gray-500">
            <p>No feature importance data available</p>
          </div>
        )}
      </CardContent>
    </Card>
  );
};

/**
 * ConfidenceBreakdown Component
 * Shows confidence decomposition by source
 */
export const ConfidenceBreakdown: React.FC<{
  sources?: Record<string, number>;
  uncertainty: number;
}> = ({ sources = {}, uncertainty }) => {
  const totalConfidence = 1 - uncertainty;

  return (
    <Card className="w-full">
      <CardHeader>
        <CardTitle className="text-base">Confidence Breakdown</CardTitle>
        <CardDescription>Decomposition of model confidence</CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Overall Confidence */}
        <div className="p-4 bg-blue-50 rounded-lg border border-blue-200">
          <div className="flex justify-between items-center mb-2">
            <span className="text-sm font-medium text-gray-700">
              Overall Confidence
            </span>
            <span className="text-lg font-bold text-blue-600">
              {(totalConfidence * 100).toFixed(1)}%
            </span>
          </div>
          <div className="w-full h-3 bg-gray-200 rounded-full overflow-hidden">
            <div
              className="h-full bg-gradient-to-r from-blue-400 to-blue-600"
              style={{ width: `${totalConfidence * 100}%` }}
            />
          </div>
        </div>

        {/* Confidence Sources */}
        {Object.keys(sources).length > 0 && (
          <div className="space-y-3">
            <h4 className="text-sm font-semibold text-gray-700">
              Confidence Sources:
            </h4>
            {Object.entries(sources)
              .sort(([, a], [, b]) => b - a)
              .map(([source, contribution]) => (
                <div key={source} className="space-y-1">
                  <div className="flex justify-between text-sm">
                    <span className="capitalize text-gray-600">{source}</span>
                    <span className="font-medium">
                      {(contribution * 100).toFixed(1)}%
                    </span>
                  </div>
                  <div className="w-full h-2 bg-gray-200 rounded-full overflow-hidden">
                    <div
                      className="h-full bg-green-500 rounded-full"
                      style={{ width: `${contribution * 100}%` }}
                    />
                  </div>
                </div>
              ))}
          </div>
        )}

        {/* Uncertainty */}
        <div className="p-3 bg-yellow-50 rounded border border-yellow-200">
          <div className="flex justify-between text-sm">
            <span className="text-gray-700">Prediction Uncertainty</span>
            <span className="font-medium text-yellow-700">
              {(uncertainty * 100).toFixed(1)}%
            </span>
          </div>
        </div>
      </CardContent>
    </Card>
  );
};

/**
 * XAIModal Component
 * Comprehensive modal displaying all XAI components
 */
export const XAIModal: React.FC<{
  isOpen: boolean;
  onClose: () => void;
  explanation: ExplanationData;
  attendionMapData?: string;
}> = ({ isOpen, onClose, explanation, attendionMapData }) => {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center p-4">
      <div className="bg-white rounded-lg max-w-4xl max-h-[90vh] overflow-y-auto shadow-xl">
        {/* Header */}
        <div className="sticky top-0 bg-white border-b p-6 flex justify-between items-center">
          <div>
            <h2 className="text-2xl font-bold text-gray-900">
              {explanation.task} Prediction Explanation
            </h2>
            <p className="text-sm text-gray-500 mt-1">
              Generated: {new Date(explanation.timestamp).toLocaleString()}
            </p>
          </div>
          <button
            onClick={onClose}
            className="text-gray-500 hover:text-gray-700 text-2xl font-bold"
          >
            ×
          </button>
        </div>

        {/* Content */}
        <div className="p-6 space-y-6">
          <Tabs defaultValue="explanation" className="w-full">
            <TabsList className="grid w-full grid-cols-4">
              <TabsTrigger value="explanation">Explanation</TabsTrigger>
              <TabsTrigger value="features">Features</TabsTrigger>
              <TabsTrigger value="confidence">Confidence</TabsTrigger>
              <TabsTrigger value="visual">Visual</TabsTrigger>
            </TabsList>

            {/* Explanation Tab */}
            <TabsContent value="explanation" className="space-y-4">
              <ExplanationPanel explanation={explanation} />
            </TabsContent>

            {/* Features Tab */}
            <TabsContent value="features" className="space-y-4">
              <FeatureImportanceChart
                features={explanation.top_contributing_features}
              />
            </TabsContent>

            {/* Confidence Tab */}
            <TabsContent value="confidence" className="space-y-4">
              <ConfidenceBreakdown
                sources={explanation.confidence_sources}
                uncertainty={explanation.prediction_uncertainty}
              />
            </TabsContent>

            {/* Visual Tab */}
            <TabsContent value="visual" className="space-y-4">
              <AttentionMapViewer
                mapData={attendionMapData}
                mapType="attention"
              />
            </TabsContent>
          </Tabs>
        </div>

        {/* Footer */}
        <div className="border-t p-6 bg-gray-50 flex justify-end gap-3">
          <button
            onClick={onClose}
            className="px-4 py-2 text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50"
          >
            Close
          </button>
          <button
            onClick={() => {
              navigator.clipboard.writeText(JSON.stringify(explanation));
              alert('Explanation copied to clipboard');
            }}
            className="px-4 py-2 text-white bg-blue-600 rounded-lg hover:bg-blue-700"
          >
            Copy JSON
          </button>
        </div>
      </div>
    </div>
  );
};

/**
 * XAIInfoBanner Component
 * Shows quick XAI info in a compact banner
 */
export const XAIInfoBanner: React.FC<{
  explanation: ExplanationData;
  onExplore: () => void;
}> = ({ explanation, onExplore }) => {
  const getConfidenceEmoji = (level: string) => {
    switch (level) {
      case 'high':
        return '✅';
      case 'medium':
        return '⚠️';
      case 'low':
        return '❌';
      default:
        return 'ℹ️';
    }
  };

  return (
    <div className="bg-gradient-to-r from-blue-50 to-purple-50 border-l-4 border-blue-500 p-4 rounded-r-lg">
      <div className="flex items-start justify-between gap-4">
        <div className="flex items-start gap-3 flex-1">
          <Brain className="w-5 h-5 text-blue-600 mt-0.5 flex-shrink-0" />
          <div className="flex-1">
            <div className="font-semibold text-gray-900 flex items-center gap-2">
              {getConfidenceEmoji(explanation.confidence_level)}
              AI Explanation Available
            </div>
            <p className="text-sm text-gray-600 mt-1">
              {explanation.explanation_text}
            </p>
          </div>
        </div>
        <button
          onClick={onExplore}
          className="px-3 py-2 text-sm font-medium text-blue-600 hover:text-blue-700 hover:bg-blue-100 rounded-lg transition-colors flex-shrink-0"
        >
          Explore <ChevronDown className="w-4 h-4 ml-1" />
        </button>
      </div>
    </div>
  );
};
