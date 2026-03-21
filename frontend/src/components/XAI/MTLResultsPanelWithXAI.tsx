import React, { useState, useEffect } from 'react';
import {
  AlertCircle, Brain, ChevronDown, ChevronUp, Loader, Eye,
  Glasses, Target, FlaskConical, TrendingUp, ShieldAlert,
  Info, BookOpen, HeartPulse, CheckCircle, Layers, Sparkles,
  BarChart3, Activity
} from 'lucide-react';
import {
  XAIModal,
  XAIInfoBanner,
  ExplanationPanel,
  ConfidenceBreakdown,
  Card,
  CardHeader,
  CardTitle,
  CardDescription,
  CardContent,
} from './ExplanationComponents';

// ─── Clinical Knowledge ───────────────────────────────────────────────────────
const DR_STAGES = [
  {
    grade: 0, label: 'No DR', shortLabel: 'None', color: 'green',
    desc: 'No diabetic retinopathy detected. Retinal vasculature appears normal without signs of diabetic damage.',
    action: 'Routine annual diabetic eye exam. Maintain HbA1c < 7%. Blood pressure control.',
  },
  {
    grade: 1, label: 'Mild NPDR', shortLabel: 'Mild', color: 'yellow',
    desc: 'Microaneurysms present — small balloon-like swellings in retinal blood vessels. Earliest detectable change.',
    action: 'Follow-up in 9–12 months. Optimise glycaemic control. HbA1c target < 7%.',
  },
  {
    grade: 2, label: 'Moderate NPDR', shortLabel: 'Moderate', color: 'orange',
    desc: 'More blocked blood vessels — some areas of retina becoming poorly nourished. Haemorrhages may be visible.',
    action: 'Ophthalmology referral within 3–6 months. Fluorescein angiography recommended. Intensive diabetes management.',
  },
  {
    grade: 3, label: 'Severe NPDR', shortLabel: 'Severe', color: 'red',
    desc: 'Large areas of retina deprived of blood supply. Body attempts to grow new blood vessels (pre-proliferative stage).',
    action: 'Urgent referral within 1 month. Consider pan-retinal photocoagulation. Close monitoring every 3 months.',
  },
  {
    grade: 4, label: 'Proliferative DR', shortLabel: 'PDR', color: 'rose',
    desc: 'New fragile blood vessels growing on retinal surface (neovascularisation). High risk of vitreous haemorrhage and retinal detachment.',
    action: 'URGENT — Refer within 1 week. Pan-retinal photocoagulation or anti-VEGF therapy. Vitreoretinal surgery may be required.',
  },
];

function getDRStage(prediction: number) {
  return DR_STAGES[Math.min(prediction, 4)];
}

function getGlaucomaRisk(score: number) {
  if (score > 0.7) return { label: 'High Risk', color: 'red', desc: 'Significant optic nerve changes or high cup-to-disc ratio detected. Urgent IOP measurement and visual field testing required.', action: 'Urgent ophthalmology referral. Tonometry, OCT nerve fibre layer, 24-2 visual field.' };
  if (score > 0.4) return { label: 'Moderate Risk', color: 'amber', desc: 'Suspicious optic disc morphology detected. Further evaluation needed to exclude early glaucoma.', action: 'Schedule comprehensive glaucoma evaluation within 3 months. IOP monitoring.' };
  return { label: 'Low Risk', color: 'green', desc: 'Optic disc appearance within normal limits. No significant cup-to-disc ratio enlargement or nerve fibre layer thinning.', action: 'Routine annual monitoring. Baseline optic disc photography recommended.' };
}

function getRefractionType(sphere: number, cylinder: number) {
  const absC = Math.abs(cylinder);
  if (sphere <= -6) return { type: 'High Myopia', desc: 'High nearsightedness — elevated risk of retinal detachment, myopic maculopathy, and glaucoma. Retinal periphery examination essential.', icon: '🔴' };
  if (sphere < -0.5) return { type: 'Myopia', desc: 'Nearsighted — light focuses in front of retina. Distant objects blurry. Common and treatable with concave lenses.', icon: '🔵' };
  if (sphere > 3) return { type: 'Significant Hyperopia', desc: 'Significant farsightedness — narrow-angle glaucoma risk. Slit-lamp exam to assess iridocorneal angle recommended.', icon: '🟠' };
  if (sphere > 0.5) return { type: 'Hyperopia', desc: 'Farsighted — light focuses behind retina. Near objects blurry. Convex lenses correct this.', icon: '🔵' };
  if (absC >= 0.75) return { type: 'Astigmatism', desc: 'Irregular corneal curvature causing blurry/distorted vision at all distances. Toric lenses required.', icon: '🟡' };
  return { type: 'Emmetropia (Normal)', desc: 'Normal refraction — light focuses precisely on retina. Excellent vision without correction.', icon: '🟢' };
}

function getLensRecommendation(sphere: number, cylinder: number) {
  const absS = Math.abs(sphere); const absC = Math.abs(cylinder);
  if (absS < 0.5 && absC < 0.75) return { needed: false, type: 'None required', detail: 'Visual acuity is within normal limits. No corrective lenses needed.' };
  if (absC > 2) return { needed: true, type: 'Toric lenses', detail: 'Significant astigmatism requires toric lenses. Precise axis alignment is critical. Custom-prescribed glasses or toric contact lenses.' };
  if (absS >= 6) return { needed: true, type: 'High-index lenses (1.67–1.74)', detail: 'High power requires high-index lenses to reduce thickness and weight. Anti-reflective coating essential. Frame selection important to minimise edge thickness.' };
  if (absS >= 3) return { needed: true, type: 'Mid-index lenses (1.60)', detail: 'Moderate power — 1.60 index recommended for comfort. Consider progressive lenses if near correction also needed.' };
  return { needed: true, type: 'Standard single-vision (1.50)', detail: 'Low to moderate correction — standard lenses suitable. Blue-light filtering recommended if significant screen time.' };
}

// ─── Confidence Badge ─────────────────────────────────────────────────────────
function ConfidenceBadge({ value }: { value: number }) {
  const pct = value * 100;
  const color = pct >= 85 ? 'text-green-700 bg-green-50 border-green-200' : pct >= 70 ? 'text-amber-700 bg-amber-50 border-amber-200' : 'text-red-700 bg-red-50 border-red-200';
  const label = pct >= 85 ? 'High' : pct >= 70 ? 'Medium' : 'Low';
  return (
    <span className={`text-xs font-bold border px-2 py-0.5 rounded-full ${color}`}>
      {label} ({pct.toFixed(1)}%)
    </span>
  );
}

// ─── Score Bar ────────────────────────────────────────────────────────────────
function ScoreBarMTL({ score, color }: { score: number; color: string }) {
  const gradients: Record<string, string> = {
    green: 'from-green-400 to-green-600',
    amber: 'from-amber-400 to-amber-600',
    orange: 'from-orange-400 to-orange-600',
    red: 'from-red-400 to-red-600',
    rose: 'from-rose-500 to-rose-700',
    blue: 'from-blue-400 to-blue-600',
    purple: 'from-purple-400 to-purple-600',
  };
  return (
    <div className="w-full h-2.5 bg-slate-100 rounded-full overflow-hidden">
      <div
        className={`h-full rounded-full bg-gradient-to-r ${gradients[color] || gradients.blue} transition-all duration-700`}
        style={{ width: `${Math.min(score * 100, 100)}%` }}
      />
    </div>
  );
}

// ─── Section Expandable ───────────────────────────────────────────────────────
function ExpandSection({ title, badge, badgeColor, isOpen, onToggle, children }: {
  title: string; badge?: string; badgeColor?: string;
  isOpen: boolean; onToggle: () => void; children: React.ReactNode;
}) {
  return (
    <div className={`rounded-2xl border overflow-hidden transition-all ${isOpen ? 'border-indigo-200 shadow-md' : 'border-gray-200 hover:border-gray-300'} bg-white`}>
      <button className="w-full text-left px-5 py-4 flex items-center justify-between gap-3" onClick={onToggle}>
        <span className="font-bold text-gray-900 text-sm">{title}</span>
        <div className="flex items-center gap-2">
          {badge && (
            <span className={`text-xs font-bold px-2.5 py-0.5 rounded-full border ${badgeColor || 'bg-gray-100 text-gray-600 border-gray-200'}`}>
              {badge}
            </span>
          )}
          {isOpen ? <ChevronUp className="w-4 h-4 text-gray-400" /> : <ChevronDown className="w-4 h-4 text-gray-400" />}
        </div>
      </button>
      {isOpen && <div className="border-t border-gray-100 px-5 pb-5 pt-4 bg-gray-50/30">{children}</div>}
    </div>
  );
}

interface MTLPredictionResult {
  prediction_id: string;
  dr_prediction: number;
  glaucoma_prediction: number;
  refraction_sphere: number;
  refraction_cylinder: number;
  refraction_axis: number;
  dr_confidence: number;
  glaucoma_confidence: number;
  refraction_confidence: number;
  dr_classes: Record<string, number>;
}

/**
 * Enhanced MTLResultsPanel with XAI Integration
 * Displays multi-task learning results with full clinical detail & explainability
 */
export const MTLResultsPanelWithXAI: React.FC<{
  results: MTLPredictionResult;
  onRequestReview?: (predictionId: string) => void;
}> = ({ results, onRequestReview }) => {
  const [showXAIModal, setShowXAIModal] = useState(false);
  const [selectedTask, setSelectedTask] = useState<'dr' | 'glaucoma' | 'refraction'>('dr');
  const [explanations, setExplanations] = useState<Record<string, any>>({});
  const [loading, setLoading] = useState(false);
  const [expanded, setExpanded] = useState<Record<string, boolean>>({ dr: true });
  const [activeTab, setActiveTab] = useState<'results' | 'explanation' | 'recommendations'>('results');

  useEffect(() => {
    if (showXAIModal && !explanations[selectedTask]) {
      fetchExplanation();
    }
  }, [showXAIModal, selectedTask]);

  const fetchExplanation = async () => {
    setLoading(true);
    try {
      let endpoint = '';
      let payload: Record<string, unknown> = { prediction_id: results.prediction_id, confidence: 0 };
      if (selectedTask === 'dr') {
        endpoint = '/api/ml/xai/explain/dr';
        payload = { ...payload, dr_prediction: results.dr_prediction, confidence: results.dr_confidence, class_probabilities: results.dr_classes };
      } else if (selectedTask === 'glaucoma') {
        endpoint = '/api/ml/xai/explain/glaucoma';
        payload = { ...payload, glaucoma_score: results.glaucoma_prediction, confidence: results.glaucoma_confidence };
      } else {
        endpoint = '/api/ml/xai/explain/refraction';
        payload = { ...payload, sphere: results.refraction_sphere, cylinder: results.refraction_cylinder, axis: results.refraction_axis, confidence: results.refraction_confidence };
      }
      const response = await fetch(endpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify(payload),
      });
      if (!response.ok) throw new Error('Failed to fetch explanation');
      const explanation = await response.json();
      setExplanations(prev => ({ ...prev, [selectedTask]: explanation }));
    } catch (error) {
      console.error('Error fetching XAI explanation:', error);
    } finally {
      setLoading(false);
    }
  };

  const toggle = (section: string) => setExpanded(prev => ({ ...prev, [section]: !prev[section] }));

  // Derived data
  const drStage = getDRStage(results.dr_prediction);
  const glaucomaInfo = getGlaucomaRisk(results.glaucoma_prediction);
  const refractionType = getRefractionType(results.refraction_sphere, results.refraction_cylinder);
  const lensRec = getLensRecommendation(results.refraction_sphere, results.refraction_cylinder);

  // Overall risk level
  const overallRisk = results.dr_prediction >= 3 || results.glaucoma_prediction > 0.7 ? 'High'
    : results.dr_prediction >= 2 || results.glaucoma_prediction > 0.4 ? 'Moderate' : 'Low';

  const overallColor = overallRisk === 'High' ? 'text-red-700 bg-red-50 border-red-200'
    : overallRisk === 'Moderate' ? 'text-amber-700 bg-amber-50 border-amber-200'
    : 'text-green-700 bg-green-50 border-green-200';

  return (
    <div className="space-y-4 w-full">
      {/* ── Summary Header ─────────────────── */}
      <div className="bg-gradient-to-br from-slate-800 to-slate-900 rounded-2xl p-5 text-white">
        <div className="flex items-center gap-3 mb-3">
          <div className="p-2 bg-white/10 rounded-xl">
            <Brain className="w-5 h-5" />
          </div>
          <div>
            <div className="font-bold text-base">Multi-Task Learning Analysis</div>
            <div className="text-slate-400 text-xs">EfficientNet-B3 · Simultaneous inference</div>
          </div>
          <span className={`ml-auto text-xs font-bold px-3 py-1.5 rounded-full border ${overallColor}`}>
            {overallRisk} Risk
          </span>
        </div>
        {/* Compact stats row */}
        <div className="grid grid-cols-3 gap-3">
          {[
            { label: 'DR Grade', value: drStage.shortLabel, color: drStage.grade === 0 ? 'text-green-400' : drStage.grade <= 2 ? 'text-amber-400' : 'text-red-400' },
            { label: 'Glaucoma', value: `${(results.glaucoma_prediction * 100).toFixed(0)}%`, color: glaucomaInfo.color === 'red' ? 'text-red-400' : glaucomaInfo.color === 'amber' ? 'text-amber-400' : 'text-green-400' },
            { label: 'Sphere', value: `${results.refraction_sphere >= 0 ? '+' : ''}${results.refraction_sphere.toFixed(2)}D`, color: 'text-sky-400' },
          ].map(({ label, value, color }) => (
            <div key={label} className="bg-white/5 rounded-xl p-3 text-center">
              <div className={`text-base font-bold ${color}`}>{value}</div>
              <div className="text-slate-400 text-xs mt-0.5">{label}</div>
            </div>
          ))}
        </div>
      </div>

      {/* ── Tabs ────────────────────────────── */}
      <div className="flex gap-1 bg-gray-100 p-1 rounded-2xl">
        {([
          ['results', 'Predictions', BarChart3],
          ['explanation', 'XAI Explain', Brain],
          ['recommendations', 'Actions', CheckCircle],
        ] as const).map(([tab, label, Icon]) => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            className={`flex-1 py-2 text-xs font-semibold rounded-xl flex items-center justify-center gap-1.5 transition-all ${activeTab === tab ? 'bg-white text-indigo-700 shadow-sm' : 'text-gray-500 hover:text-gray-700'}`}
          >
            <Icon className="w-3.5 h-3.5" /> {label}
          </button>
        ))}
      </div>

      {/* ══════ PREDICTIONS TAB ══════ */}
      {activeTab === 'results' && (
        <div className="space-y-3">
          {/* DR Card */}
          <ExpandSection
            title="Diabetic Retinopathy (DR)"
            badge={drStage.label}
            badgeColor={
              drStage.grade === 0 ? 'bg-green-100 text-green-700 border-green-200'
              : drStage.grade <= 2 ? 'bg-amber-100 text-amber-700 border-amber-200'
              : 'bg-red-100 text-red-700 border-red-200'
            }
            isOpen={expanded['dr'] ?? true}
            onToggle={() => toggle('dr')}
          >
            {/* Grade visual */}
            <div className="mb-4">
              <div className="flex items-center justify-between mb-2">
                <div className="text-xs font-bold text-gray-500 uppercase tracking-wide">Severity Stage</div>
                <ConfidenceBadge value={results.dr_confidence} />
              </div>
              {/* 5-stage scale */}
              <div className="flex gap-1 mb-3 h-3">
                {DR_STAGES.map((s, i) => (
                  <div
                    key={s.grade}
                    className={`flex-1 rounded-full transition-all ${i <= results.dr_prediction ? (i <= 1 ? 'bg-green-400' : i === 2 ? 'bg-amber-500' : i === 3 ? 'bg-red-500' : 'bg-rose-700') : 'bg-gray-200'}`}
                  />
                ))}
              </div>
              <div className="flex justify-between text-xs text-gray-400">
                <span>None</span><span>Mild</span><span>Moderate</span><span>Severe</span><span>PDR</span>
              </div>
            </div>

            {/* Current stage detail */}
            <div className={`p-3 rounded-xl border mb-4 ${drStage.grade === 0 ? 'bg-green-50 border-green-200' : drStage.grade <= 2 ? 'bg-amber-50 border-amber-200' : 'bg-red-50 border-red-200'}`}>
              <div className="text-xs font-bold text-gray-700 mb-1">What this means:</div>
              <p className="text-xs text-gray-600 leading-relaxed">{drStage.desc}</p>
            </div>

            {/* Class probability bars */}
            {results.dr_classes && Object.keys(results.dr_classes).length > 0 && (
              <div className="mb-4 space-y-2">
                <div className="text-xs font-bold text-gray-500 uppercase tracking-wide">Class Probabilities</div>
                {DR_STAGES.map(stage => {
                  const key = Object.keys(results.dr_classes).find(k => k.toLowerCase().includes(stage.shortLabel.toLowerCase()) || k === String(stage.grade));
                  const val = key ? results.dr_classes[key] : (results.dr_prediction === stage.grade ? results.dr_confidence : (1 - results.dr_confidence) / 4);
                  return (
                    <div key={stage.grade} className="space-y-0.5">
                      <div className="flex justify-between text-xs">
                        <span className={`font-medium ${results.dr_prediction === stage.grade ? 'text-gray-900' : 'text-gray-500'}`}>{stage.label}</span>
                        <span className={`font-bold ${results.dr_prediction === stage.grade ? 'text-gray-900' : 'text-gray-400'}`}>{(val * 100).toFixed(1)}%</span>
                      </div>
                      <ScoreBarMTL score={val} color={stage.grade === 0 ? 'green' : stage.grade <= 2 ? 'amber' : stage.grade === 3 ? 'red' : 'rose'} />
                    </div>
                  );
                })}
              </div>
            )}

            {/* XAI prompt */}
            <button onClick={() => { setSelectedTask('dr'); setShowXAIModal(true); }}
              className="w-full mt-2 px-4 py-3 text-left bg-gradient-to-r from-indigo-50 to-blue-50 border border-indigo-200 rounded-xl hover:border-indigo-300 transition-colors">
              <div className="flex items-center gap-2 text-indigo-700 font-semibold text-sm">
                <Sparkles className="w-4 h-4" /> View AI Explanation for DR
              </div>
              <p className="text-xs text-indigo-600 mt-0.5">See which retinal features influenced this prediction</p>
            </button>

            {results.dr_confidence < 0.70 && (
              <div className="mt-3 p-3 bg-yellow-50 border border-yellow-200 rounded-xl flex gap-2">
                <AlertCircle className="w-4 h-4 text-yellow-600 flex-shrink-0 mt-0.5" />
                <p className="text-xs text-yellow-800"><strong>Low Confidence:</strong> Below 70% — expert review strongly recommended before clinical decision.</p>
              </div>
            )}
          </ExpandSection>

          {/* Glaucoma Card */}
          <ExpandSection
            title="Glaucoma Risk Assessment"
            badge={glaucomaInfo.label}
            badgeColor={
              glaucomaInfo.color === 'red' ? 'bg-red-100 text-red-700 border-red-200'
              : glaucomaInfo.color === 'amber' ? 'bg-amber-100 text-amber-700 border-amber-200'
              : 'bg-green-100 text-green-700 border-green-200'
            }
            isOpen={expanded['glaucoma'] ?? false}
            onToggle={() => toggle('glaucoma')}
          >
            <div className="mb-4">
              <div className="flex items-center justify-between mb-2">
                <div className="text-xs font-bold text-gray-500 uppercase tracking-wide">Risk Score</div>
                <ConfidenceBadge value={results.glaucoma_confidence} />
              </div>
              <div className="flex items-center gap-3 mb-1">
                <div className="flex-1 h-3 bg-gray-100 rounded-full overflow-hidden">
                  <div
                    className="h-full rounded-full bg-gradient-to-r from-green-400 via-amber-400 to-red-500"
                    style={{ width: `${results.glaucoma_prediction * 100}%` }}
                  />
                </div>
                <span className="text-sm font-bold text-gray-700 w-12 text-right">
                  {(results.glaucoma_prediction * 100).toFixed(1)}%
                </span>
              </div>
              <div className="flex justify-between text-xs text-gray-400">
                <span>Low (&lt;40%)</span><span>Moderate (40–70%)</span><span>High (&gt;70%)</span>
              </div>
            </div>

            <div className={`p-3 rounded-xl border mb-4 ${glaucomaInfo.color === 'red' ? 'bg-red-50 border-red-200' : glaucomaInfo.color === 'amber' ? 'bg-amber-50 border-amber-200' : 'bg-green-50 border-green-200'}`}>
              <div className="text-xs font-bold text-gray-700 mb-1">Clinical Interpretation:</div>
              <p className="text-xs text-gray-600 leading-relaxed">{glaucomaInfo.desc}</p>
            </div>

            <div className="p-3 bg-gray-50 rounded-xl border border-gray-200 mb-3">
              <div className="text-xs font-bold text-gray-500 mb-2 flex items-center gap-1">
                <Info className="w-3 h-3" /> What the AI analyses for glaucoma:
              </div>
              <ul className="space-y-1.5 text-xs text-gray-600">
                <li className="flex gap-2"><span className="text-purple-500 font-bold">→</span> Cup-to-Disc Ratio (CDR) — elevated CDR {'>'} 0.6 is suspicious</li>
                <li className="flex gap-2"><span className="text-purple-500 font-bold">→</span> Nerve Fibre Layer (NFL) thickness — thinning indicates damage</li>
                <li className="flex gap-2"><span className="text-purple-500 font-bold">→</span> Optic disc pallor and neuroretinal rim area</li>
                <li className="flex gap-2"><span className="text-purple-500 font-bold">→</span> Peripapillary atrophy around optic disc</li>
              </ul>
            </div>

            <button onClick={() => { setSelectedTask('glaucoma'); setShowXAIModal(true); }}
              className="w-full px-4 py-3 text-left bg-gradient-to-r from-purple-50 to-pink-50 border border-purple-200 rounded-xl hover:border-purple-300 transition-colors">
              <div className="flex items-center gap-2 text-purple-700 font-semibold text-sm">
                <Sparkles className="w-4 h-4" /> View AI Explanation for Glaucoma
              </div>
            </button>
          </ExpandSection>

          {/* Refraction Card */}
          <ExpandSection
            title="Refractive Error Estimate"
            badge={refractionType.type}
            badgeColor="bg-sky-100 text-sky-700 border-sky-200"
            isOpen={expanded['refraction'] ?? false}
            onToggle={() => toggle('refraction')}
          >
            <div className="grid grid-cols-3 gap-3 mb-4">
              {[
                { label: 'Sphere', value: `${results.refraction_sphere >= 0 ? '+' : ''}${results.refraction_sphere.toFixed(2)}`, unit: 'D', bg: 'bg-sky-50 border-sky-200', text: 'text-sky-700' },
                { label: 'Cylinder', value: `${results.refraction_cylinder >= 0 ? '+' : ''}${results.refraction_cylinder.toFixed(2)}`, unit: 'D', bg: 'bg-cyan-50 border-cyan-200', text: 'text-cyan-700' },
                { label: 'Axis', value: `${results.refraction_axis.toFixed(0)}°`, unit: '', bg: 'bg-indigo-50 border-indigo-200', text: 'text-indigo-700' },
              ].map(({ label, value, unit, bg, text }) => (
                <div key={label} className={`${bg} border rounded-xl p-3 text-center`}>
                  <div className={`text-xl font-bold ${text}`}>{value}</div>
                  {unit && <div className="text-xs text-gray-400">{unit}</div>}
                  <div className="text-xs text-gray-600 mt-1">{label}</div>
                </div>
              ))}
            </div>

            <div className="flex items-center justify-between mb-3">
              <div className="text-xs font-bold text-gray-500 uppercase tracking-wide">Prediction Confidence</div>
              <ConfidenceBadge value={results.refraction_confidence} />
            </div>
            <ScoreBarMTL score={results.refraction_confidence} color="blue" />

            <div className="mt-4 p-3 bg-sky-50 border border-sky-100 rounded-xl">
              <div className="flex items-center gap-1.5 mb-1">
                <span className="text-base">{refractionType.icon}</span>
                <span className="text-xs font-bold text-sky-800">{refractionType.type}</span>
              </div>
              <p className="text-xs text-gray-600 leading-relaxed">{refractionType.desc}</p>
            </div>

            <div className={`mt-3 p-3 rounded-xl border ${lensRec.needed ? 'bg-indigo-50 border-indigo-200' : 'bg-green-50 border-green-200'}`}>
              <div className="flex items-center gap-1.5 mb-1">
                <Glasses className="w-4 h-4 text-indigo-600" />
                <span className="text-xs font-bold text-gray-800">Spectacle Recommendation: {lensRec.type}</span>
              </div>
              <p className="text-xs text-gray-600 leading-relaxed">{lensRec.detail}</p>
            </div>

            <button onClick={() => { setSelectedTask('refraction'); setShowXAIModal(true); }}
              className="w-full mt-3 px-4 py-3 text-left bg-gradient-to-r from-emerald-50 to-cyan-50 border border-emerald-200 rounded-xl hover:border-emerald-300 transition-colors">
              <div className="flex items-center gap-2 text-emerald-700 font-semibold text-sm">
                <Sparkles className="w-4 h-4" /> View AI Explanation for Refraction
              </div>
            </button>
          </ExpandSection>
        </div>
      )}

      {/* ══════ XAI EXPLANATION TAB ══════ */}
      {activeTab === 'explanation' && (
        <div className="space-y-3">
          <div className="p-4 bg-indigo-50 border border-indigo-100 rounded-2xl">
            <div className="flex gap-2 mb-2">
              <Info className="w-4 h-4 text-indigo-600 flex-shrink-0 mt-0.5" />
              <span className="text-sm font-bold text-indigo-800">About XAI (Explainable AI)</span>
            </div>
            <p className="text-xs text-indigo-700 leading-relaxed">
              The AI provides detailed reasoning for each prediction using gradient-based attention maps and confidence scoring. Each task (DR, Glaucoma, Refraction) can be explained independently.
            </p>
          </div>

          {/* Task selector */}
          <div className="flex gap-1 bg-gray-100 p-1 rounded-xl">
            {(['dr', 'glaucoma', 'refraction'] as const).map(task => (
              <button
                key={task}
                onClick={() => setSelectedTask(task)}
                className={`flex-1 py-2 text-xs font-semibold rounded-lg capitalize transition-all ${selectedTask === task ? 'bg-white text-indigo-700 shadow-sm' : 'text-gray-500 hover:text-gray-700'}`}
              >
                {task === 'dr' ? 'DR Grading' : task === 'glaucoma' ? 'Glaucoma' : 'Refraction'}
              </button>
            ))}
          </div>

          {loading ? (
            <div className="flex justify-center py-8">
              <Loader className="w-6 h-6 animate-spin text-indigo-600" />
            </div>
          ) : explanations[selectedTask] ? (
            <div className="space-y-3">
              <ExplanationPanel explanation={explanations[selectedTask]} />
              {explanations[selectedTask]?.top_contributing_features && (
                <div className="p-4 bg-slate-50 border border-slate-200 rounded-xl space-y-2">
                  <div className="text-xs font-bold text-slate-600 uppercase tracking-wide">Top Contributing Features</div>
                  {explanations[selectedTask].top_contributing_features.map((f: any, i: number) => (
                    <div key={i} className="space-y-0.5">
                      <div className="flex justify-between text-xs text-slate-700">
                        <span className="font-medium">{f.feature.replace(/_/g, ' ')}</span>
                        <span className="font-bold">{(f.importance * 100).toFixed(1)}%</span>
                      </div>
                      <ScoreBarMTL score={f.importance} color="blue" />
                    </div>
                  ))}
                </div>
              )}
            </div>
          ) : (
            <div className="flex flex-col items-center justify-center py-8 gap-3">
              <Brain className="w-10 h-10 text-indigo-300" />
              <p className="text-sm text-gray-500 text-center">Load the explanation for <strong className="text-gray-700 capitalize">{selectedTask === 'dr' ? 'DR Grading' : selectedTask === 'glaucoma' ? 'Glaucoma Risk' : 'Refractive Error'}</strong></p>
              <button
                onClick={() => { setShowXAIModal(true); fetchExplanation(); }}
                className="px-4 py-2 bg-indigo-600 text-white text-sm font-semibold rounded-xl hover:bg-indigo-700 transition-colors"
              >
                Load Explanation
              </button>
            </div>
          )}
        </div>
      )}

      {/* ══════ RECOMMENDATIONS TAB ══════ */}
      {activeTab === 'recommendations' && (
        <div className="space-y-3">
          {/* Overall Risk */}
          <div className={`p-4 rounded-2xl border ${overallRisk === 'High' ? 'bg-red-50 border-red-200' : overallRisk === 'Moderate' ? 'bg-amber-50 border-amber-200' : 'bg-green-50 border-green-200'}`}>
            <div className="flex gap-3">
              {overallRisk === 'High' ? <ShieldAlert className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
                : overallRisk === 'Moderate' ? <AlertCircle className="w-5 h-5 text-amber-600 flex-shrink-0 mt-0.5" />
                : <CheckCircle className="w-5 h-5 text-green-600 flex-shrink-0 mt-0.5" />}
              <div>
                <div className={`font-bold text-sm ${overallRisk === 'High' ? 'text-red-800' : overallRisk === 'Moderate' ? 'text-amber-800' : 'text-green-800'}`}>
                  {overallRisk === 'High' ? 'Urgent Clinical Attention Required' : overallRisk === 'Moderate' ? 'Clinical Review Recommended' : 'Routine Monitoring Sufficient'}
                </div>
                <p className={`text-xs mt-1 leading-relaxed ${overallRisk === 'High' ? 'text-red-700' : overallRisk === 'Moderate' ? 'text-amber-700' : 'text-green-700'}`}>
                  {overallRisk === 'High' ? 'Significant pathology detected across multiple screening categories. Immediate ophthalmology referral is required.'
                    : overallRisk === 'Moderate' ? 'Moderate findings detected. Schedule a comprehensive ophthalmology assessment within 3 months.'
                    : 'All screening parameters within acceptable range. Continue annual eye exams and diabetes/blood pressure monitoring.'}
                </p>
              </div>
            </div>
          </div>

          {/* DR Action */}
          <div className="p-4 bg-white border border-gray-200 rounded-2xl space-y-2">
            <div className="flex items-center gap-2">
              <FlaskConical className="w-4 h-4 text-amber-600" />
              <span className="text-sm font-bold text-gray-800">DR: {drStage.label}</span>
            </div>
            <p className="text-xs text-gray-600 leading-relaxed pl-6">{drStage.action}</p>
          </div>

          {/* Glaucoma Action */}
          <div className="p-4 bg-white border border-gray-200 rounded-2xl space-y-2">
            <div className="flex items-center gap-2">
              <Target className="w-4 h-4 text-purple-600" />
              <span className="text-sm font-bold text-gray-800">Glaucoma: {glaucomaInfo.label}</span>
            </div>
            <p className="text-xs text-gray-600 leading-relaxed pl-6">{glaucomaInfo.action}</p>
          </div>

          {/* Spectacles Action */}
          <div className="p-4 bg-white border border-gray-200 rounded-2xl space-y-2">
            <div className="flex items-center gap-2">
              <Glasses className="w-4 h-4 text-sky-600" />
              <span className="text-sm font-bold text-gray-800">Spectacles: {lensRec.type}</span>
            </div>
            <p className="text-xs text-gray-600 leading-relaxed pl-6">{lensRec.detail}</p>
          </div>

          {/* Request Expert Review */}
          {onRequestReview && (
            <button
              onClick={() => onRequestReview(results.prediction_id)}
              className="w-full px-4 py-3 bg-gradient-to-r from-blue-600 to-indigo-600 text-white rounded-xl font-semibold text-sm hover:from-blue-700 hover:to-indigo-700 transition-all shadow-md shadow-blue-200 flex items-center justify-center gap-2"
            >
              <Activity className="w-4 h-4" /> Request Expert Ophthalmologist Review
            </button>
          )}

          <div className="p-3 bg-amber-50 border border-amber-200 rounded-xl">
            <div className="flex gap-2 text-xs text-amber-700">
              <AlertCircle className="w-4 h-4 flex-shrink-0 mt-0.5" />
              <span><strong>Disclaimer:</strong> This AI analysis is a screening tool only. Clinical decisions must be made by a qualified ophthalmologist with full patient history.</span>
            </div>
          </div>
        </div>
      )}

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
