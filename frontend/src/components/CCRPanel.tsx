import React, { useState, useEffect } from 'react';
import { TrendingUp, AlertCircle, CheckCircle, XCircle } from 'lucide-react';

interface ExpertConcordance {
  expert_id: string;
  dr_agreement: number;
  glaucoma_agreement: number;
  refraction_agreement: number;
  avg_agreement: number;
}

interface CCRMetrics {
  global_ccr: number;
  total_cases: number;
  cases_above_threshold: number;
  cases_below_threshold: number;
  h3_hypothesis_status: 'PASS' | 'FAIL' | 'PENDING';
  expert_metrics: ExpertConcordance[];
  task_specific_ccr: {
    dr_ccr: number;
    glaucoma_ccr: number;
    refraction_ccr: number;
  };
  confidence_interval: {
    lower: number;
    upper: number;
  };
}

interface CCRPanelProps {
  showDetails?: boolean;
}

/**
 * Clinical Concordance Rate (CCR) Panel (Week 1 - P0.5)
 * 
 * Displays H3 hypothesis validation metrics:
 * - Global CCR across expert panel
 * - Task-specific CCR (DR, Glaucoma, Refraction)
 * - Individual expert performance
 * - H3 status: "PASS" if CCR ≥ 85%, "FAIL" if < 85%, "PENDING" if insufficient data
 * 
 * Target: CCR ≥ 85% (clinical grade decision support)
 */
export const CCRPanel: React.FC<CCRPanelProps> = ({ showDetails = true }) => {
  const [metrics, setMetrics] = useState<CCRMetrics | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchCCRMetrics();
  }, []);

  const fetchCCRMetrics = async () => {
    try {
      const response = await fetch('/api/clinical/concordance/metrics');
      if (response.ok) {
        const data = await response.json();
        setMetrics(data);
      }
    } catch (error) {
      console.error('Failed to fetch CCR metrics:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return <div className="p-6 text-center text-gray-500">Loading CCR metrics...</div>;
  }

  if (!metrics) {
    return <div className="p-6 text-center text-gray-500">No CCR data available</div>;
  }

  const h3StatusDisplay = {
    'PASS': { icon: CheckCircle, color: 'bg-green-100 border-green-300 text-green-800', textColor: 'text-green-900' },
    'FAIL': { icon: XCircle, color: 'bg-red-100 border-red-300 text-red-800', textColor: 'text-red-900' },
    'PENDING': { icon: AlertCircle, color: 'bg-yellow-100 border-yellow-300 text-yellow-800', textColor: 'text-yellow-900' }
  };

  const StatusIcon = h3StatusDisplay[metrics.h3_hypothesis_status].icon;

  const ProgressBar = ({ value, isH3 = false }: { value: number; isH3?: boolean }) => {
    let color = 'bg-blue-600';
    if (isH3) {
      color = value >= 0.85 ? 'bg-green-600' : 'bg-red-600';
    }
    return (
      <div className="w-full bg-gray-200 rounded-full h-3 overflow-hidden">
        <div 
          className={`${color} h-3 rounded-full transition-all`}
          style={{ width: `${value * 100}%` }}
        />
      </div>
    );
  };

  return (
    <div className="max-w-5xl mx-auto p-6 bg-white rounded-lg shadow space-y-6">
      {/* Header */}
      <div className="flex justify-between items-start">
        <div>
          <h2 className="text-2xl font-bold flex items-center gap-2 mb-1">
            <TrendingUp className="text-blue-600" />
            Clinical Concordance Rate (H3)
          </h2>
          <p className="text-sm text-gray-600">Hypothesis: CCR ≥ 85% achievable via AI-assisted diagnosis</p>
        </div>
        <div className="text-right text-xs text-gray-500">
          <p>Cases Reviewed: {metrics.total_cases}</p>
          <p>Last Updated: {new Date().toLocaleDateString()}</p>
        </div>
      </div>

      {/* H3 Hypothesis Status (Large Display) */}
      <div className={`p-6 border-2 rounded-lg ${h3StatusDisplay[metrics.h3_hypothesis_status].color}`}>
        <div className="flex items-center gap-4">
          <StatusIcon size={40} className="flex-shrink-0" />
          <div>
            <h3 className={`text-3xl font-bold ${h3StatusDisplay[metrics.h3_hypothesis_status].textColor}`}>
              {metrics.h3_hypothesis_status}
            </h3>
            <p className="text-sm mt-1">
              {metrics.h3_hypothesis_status === 'PASS' 
                ? 'H3 Hypothesis VALIDATED: CCR ≥ 85%'
                : metrics.h3_hypothesis_status === 'FAIL'
                ? 'H3 Hypothesis NOT VALIDATED: CCR < 85%'
                : 'Insufficient data for H3 validation (need 20+ cases)'}
            </p>
          </div>
        </div>
      </div>

      {/* Main Metrics Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {/* Global CCR */}
        <div className="p-4 bg-blue-50 border border-blue-200 rounded">
          <p className="text-sm text-gray-600 mb-2">Global CCR</p>
          <div className="flex items-baseline gap-2 mb-3">
            <span className="text-3xl font-bold text-blue-900">{(metrics.global_ccr * 100).toFixed(1)}%</span>
            <span className="text-sm text-blue-700">Target: 85%</span>
          </div>
          <ProgressBar value={metrics.global_ccr} isH3={true} />
          <p className="text-xs text-gray-600 mt-2">
            {metrics.cases_above_threshold} cases ≥ threshold / {metrics.total_cases} total
          </p>
        </div>

        {/* Confidence Interval */}
        <div className="p-4 bg-purple-50 border border-purple-200 rounded">
          <p className="text-sm text-gray-600 mb-2">95% CI</p>
          <div className="font-mono text-lg text-purple-900 font-bold mb-3">
            {(metrics.confidence_interval.lower * 100).toFixed(1)}% - {(metrics.confidence_interval.upper * 100).toFixed(1)}%
          </div>
          <p className="text-xs text-purple-700">
            Margin of error: ±{((metrics.confidence_interval.upper - metrics.confidence_interval.lower) * 50).toFixed(1)}%
          </p>
        </div>

        {/* Sample Size */}
        <div className="p-4 bg-green-50 border border-green-200 rounded">
          <p className="text-sm text-gray-600 mb-2">Statistical Power</p>
          <div className="text-3xl font-bold text-green-900 mb-3">
            {metrics.total_cases >= 50 ? '★★★★★' : metrics.total_cases >= 30 ? '★★★★' : '★★★'}
          </div>
          <p className="text-xs text-green-700">
            {metrics.total_cases < 20 
              ? 'More cases needed for robust H3 validation'
              : metrics.total_cases < 50
              ? 'Good statistical power'
              : 'Excellent statistical power'}
          </p>
        </div>
      </div>

      {showDetails && (
        <>
          {/* Task-Specific CCR */}
          <div className="border-t pt-6">
            <h3 className="text-lg font-bold mb-4">CCR by Clinical Task</h3>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {[
                { name: 'Diabetic Retinopathy', value: metrics.task_specific_ccr.dr_ccr, color: 'bg-yellow-50 border-yellow-200' },
                { name: 'Glaucoma Screening', value: metrics.task_specific_ccr.glaucoma_ccr, color: 'bg-red-50 border-red-200' },
                { name: 'Refraction', value: metrics.task_specific_ccr.refraction_ccr, color: 'bg-purple-50 border-purple-200' }
              ].map((task, idx) => (
                <div key={idx} className={`p-4 border rounded ${task.color}`}>
                  <p className="text-sm font-semibold text-gray-700 mb-2">{task.name}</p>
                  <p className="text-2xl font-bold mb-2">{(task.value * 100).toFixed(1)}%</p>
                  <ProgressBar value={task.value} />
                </div>
              ))}
            </div>
          </div>

          {/* Expert Performance */}
          <div className="border-t pt-6">
            <h3 className="text-lg font-bold mb-4">Individual Expert Performance</h3>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead className="bg-gray-100 border-b">
                  <tr>
                    <th className="px-3 py-2 text-left font-semibold">Expert ID</th>
                    <th className="px-3 py-2 text-center">DR</th>
                    <th className="px-3 py-2 text-center">Glaucoma</th>
                    <th className="px-3 py-2 text-center">Refraction</th>
                    <th className="px-3 py-2 text-right font-bold">Average</th>
                  </tr>
                </thead>
                <tbody>
                  {metrics.expert_metrics.map((expert, idx) => (
                    <tr key={idx} className={idx % 2 === 0 ? 'bg-white' : 'bg-gray-50'}>
                      <td className="px-3 py-2 font-mono text-xs">{expert.expert_id}</td>
                      <td className="px-3 py-2 text-center">{(expert.dr_agreement * 100).toFixed(0)}%</td>
                      <td className="px-3 py-2 text-center">{(expert.glaucoma_agreement * 100).toFixed(0)}%</td>
                      <td className="px-3 py-2 text-center">{(expert.refraction_agreement * 100).toFixed(0)}%</td>
                      <td className="px-3 py-2 text-right font-bold text-green-700">
                        {(expert.avg_agreement * 100).toFixed(0)}%
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Information Box */}
          <div className="p-4 bg-indigo-50 border border-indigo-200 rounded text-sm text-indigo-900">
            <p className="font-semibold mb-2">About H3 Hypothesis Validation</p>
            <ul className="text-xs space-y-1 list-disc list-inside">
              <li>CCR ≥ 85% demonstrates clinical-grade decision support capability</li>
              <li>Agreement measured via 1-5 Likert scale (4-5 = agree, 1-3 = disagree)</li>
              <li>Calculated as: (Cases with ≥4 agreement) / (Total cases)</li>
              <li>Confidence interval (95% CI) accounts for sample size variability</li>
              <li>Statistical power increases with more reviewed cases (target: 50+)</li>
            </ul>
          </div>
        </>
      )}

      {/* Simple Mode Footer */}
      {!showDetails && (
        <p className="text-xs text-gray-500 text-center">
          Global CCR: {(metrics.global_ccr * 100).toFixed(1)}% | H3 Status: {metrics.h3_hypothesis_status} | Cases: {metrics.total_cases}
        </p>
      )}
    </div>
  );
};
