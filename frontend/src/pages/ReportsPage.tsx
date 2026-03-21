import React, { useState } from 'react'
import {
    FileText, Download, Printer, Eye, Activity, Brain, Glasses,
    FlaskConical, Target, CheckCircle, AlertTriangle, Info,
    TrendingUp, Calendar, User, Hospital, ShieldAlert, ClipboardList,
    X, Sparkles, BarChart3, HeartPulse, Microscope
} from 'lucide-react'

// ─── Mock / State Types ───────────────────────────────────────────────────────
interface ReportData {
    reportId: string
    date: string
    patientId?: string
    patientName?: string
    examType: string
    sphere: number
    cylinder: number
    axis: number
    drScore: number
    drGrade: number
    drStatus: 'Healthy' | 'Warning' | 'Severe'
    glaucomaScore: number
    glaucomaStatus: 'Healthy' | 'Warning' | 'Severe'
    reasoning: string[]
    confidence: number
}

// ─── Sample demo reports ──────────────────────────────────────────────────────
const DEMO_REPORTS: ReportData[] = [
    {
        reportId: 'RPT-2026-0001',
        date: '14 Mar 2026',
        patientName: 'Rahul Sharma',
        patientId: 'PT-00142',
        examType: 'Fundus Photography',
        sphere: -3.5,
        cylinder: -0.75,
        axis: 90,
        drScore: 15,
        drGrade: 0,
        drStatus: 'Healthy',
        glaucomaScore: 22,
        glaucomaStatus: 'Healthy',
        reasoning: ['No microaneurysms or haemorrhages detected', 'Optic disc cup-to-disc ratio within normal limits (0.35)', 'Retinal vasculature appears normal'],
        confidence: 94.5,
    },
    {
        reportId: 'RPT-2026-0002',
        date: '12 Mar 2026',
        patientName: 'Priya Mehta',
        patientId: 'PT-00138',
        examType: 'Fundus Photography',
        sphere: -6.25,
        cylinder: -1.5,
        axis: 180,
        drScore: 52,
        drGrade: 2,
        drStatus: 'Warning',
        glaucomaScore: 48,
        glaucomaStatus: 'Warning',
        reasoning: ['Moderate NPDR features detected — vessel changes present', 'Suspicious cup-to-disc ratio (0.6) — glaucoma workup recommended', 'High myopia (-6.25D) elevates retinal detachment risk'],
        confidence: 88.2,
    },
    {
        reportId: 'RPT-2026-0003',
        date: '10 Mar 2026',
        patientName: 'Arun Kumar',
        patientId: 'PT-00129',
        examType: 'DICOM Fundus',
        sphere: 1.5,
        cylinder: -0.25,
        axis: 45,
        drScore: 78,
        drGrade: 3,
        drStatus: 'Severe',
        glaucomaScore: 35,
        glaucomaStatus: 'Healthy',
        reasoning: ['Severe NPDR — multiple haemorrhages and venous beading detected', 'Neovascularisation signs on optic disc', 'Immediate pan-retinal photocoagulation evaluation recommended'],
        confidence: 91.7,
    },
]

// ─── Condition helpers ────────────────────────────────────────────────────────
const DR_LABELS = ['No DR', 'Mild NPDR', 'Moderate NPDR', 'Severe NPDR', 'Proliferative DR']
const DR_COLORS: Record<number, string> = { 0: 'text-green-700', 1: 'text-yellow-700', 2: 'text-orange-600', 3: 'text-red-700', 4: 'text-rose-900' }

function classifyMyopia(sphere: number) {
    if (sphere <= -9) return { label: 'High Pathological Myopia', color: 'text-red-700', bg: 'bg-red-50 border-red-200' }
    if (sphere <= -6) return { label: 'High Myopia', color: 'text-orange-700', bg: 'bg-orange-50 border-orange-200' }
    if (sphere < -3) return { label: 'Moderate Myopia', color: 'text-yellow-700', bg: 'bg-yellow-50 border-yellow-200' }
    if (sphere < 0) return { label: 'Mild Myopia', color: 'text-blue-700', bg: 'bg-blue-50 border-blue-200' }
    if (sphere < 0.5) return { label: 'Emmetropia (Normal)', color: 'text-green-700', bg: 'bg-green-50 border-green-200' }
    if (sphere < 3) return { label: 'Mild Hyperopia', color: 'text-blue-700', bg: 'bg-blue-50 border-blue-200' }
    return { label: 'Significant Hyperopia', color: 'text-orange-700', bg: 'bg-orange-50 border-orange-200' }
}

function getStatusBadge(status: 'Healthy' | 'Warning' | 'Severe') {
    if (status === 'Healthy') return 'bg-green-100 text-green-700 border-green-200'
    if (status === 'Warning') return 'bg-amber-100 text-amber-700 border-amber-200'
    return 'bg-red-100 text-red-700 border-red-200'
}

function getLensRecommendation(sphere: number, cylinder: number): string {
    const absS = Math.abs(sphere); const absC = Math.abs(cylinder)
    if (absS < 0.5 && absC < 0.75) return 'No corrective lenses required'
    if (absC > 2) return 'Toric lenses required for significant astigmatism correction'
    if (absS >= 6) return 'High-index lenses (1.67 or 1.74) recommended — thinner & lighter'
    return 'Single-vision lenses (standard 1.50 or 1.60 index) suitable'
}

function getFollowUp(drGrade: number, glaucomaScore: number, sphere: number): string {
    if (drGrade >= 3 || glaucomaScore >= 70) return '⚡ URGENT — Within 1–4 weeks'
    if (drGrade >= 2 || glaucomaScore >= 50 || sphere <= -6) return '🔶 Priority — Within 3 months'
    if (drGrade >= 1 || sphere <= -3) return '📅 Routine — 6 months'
    return '📅 Routine — 12 months'
}

// ─── Report Print View ────────────────────────────────────────────────────────
function PrintableReport({ report, onClose }: { report: ReportData; onClose: () => void }) {
    const myopia = classifyMyopia(report.sphere)
    const drLabel = DR_LABELS[Math.min(report.drGrade, 4)]
    const drColor = DR_COLORS[Math.min(report.drGrade, 4)]
    const lensRec = getLensRecommendation(report.sphere, report.cylinder)
    const followUp = getFollowUp(report.drGrade, report.glaucomaScore, report.sphere)
    const isUrgent = report.drGrade >= 3 || report.glaucomaScore >= 70

    const handleExportText = () => {
        const text = `REFRACTO AI — CLINICAL REPORT
Report ID: ${report.reportId}
Date: ${report.date}
${report.patientName ? `Patient: ${report.patientName}` : ''}${report.patientId ? ` (${report.patientId})` : ''}
Exam Type: ${report.examType}
AI Confidence: ${report.confidence.toFixed(1)}%
════════════════════════════════════════

REFRACTIVE ERROR
  Sphere:   ${report.sphere >= 0 ? '+' : ''}${report.sphere.toFixed(2)} D
  Cylinder: ${report.cylinder >= 0 ? '+' : ''}${report.cylinder.toFixed(2)} D
  Axis:     ${Math.round(report.axis)}°
  Classification: ${myopia.label}

PATHOLOGY SCREENING
  Diabetic Retinopathy: ${drLabel} (Score: ${report.drScore}/100)
  Glaucoma Risk:        ${report.glaucomaStatus} (Score: ${report.glaucomaScore}/100)

LENS RECOMMENDATION
  ${lensRec}

CLINICAL REASONING
${report.reasoning.map((r, i) => `  ${i + 1}. ${r}`).join('\n')}

RECOMMENDED FOLLOW-UP
  ${followUp}

════════════════════════════════════════
⚠️ AI-assisted report. Requires clinical verification before treatment.
Refracto AI | Powered by EfficientNet-B3 MTL`

        const blob = new Blob([text], { type: 'text/plain' })
        const url = URL.createObjectURL(blob)
        const a = document.createElement('a')
        a.href = url
        a.download = `${report.reportId}_clinical_report.txt`
        a.click()
        URL.revokeObjectURL(url)
    }

    return (
        <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-start justify-center p-4 overflow-y-auto" onClick={onClose}>
            <div className="bg-white w-full max-w-2xl rounded-3xl shadow-2xl my-4" onClick={e => e.stopPropagation()}>
                {/* Actions bar (hidden in print) */}
                <div className="flex items-center justify-between px-6 py-4 border-b border-slate-100 print:hidden">
                    <span className="font-bold text-slate-700">Clinical Report — {report.reportId}</span>
                    <div className="flex gap-2">
                        <button onClick={handleExportText}
                            className="flex items-center gap-1.5 text-sm font-medium text-slate-600 hover:text-slate-800 border border-slate-200 hover:border-slate-300 px-3 py-2 rounded-xl transition-colors">
                            <Download size={15} /> Export .txt
                        </button>
                        <button onClick={() => window.print()}
                            className="flex items-center gap-1.5 text-sm font-medium text-white bg-slate-800 hover:bg-slate-700 px-3 py-2 rounded-xl transition-colors">
                            <Printer size={15} /> Print / PDF
                        </button>
                        <button onClick={onClose} className="p-2 text-slate-400 hover:text-slate-600 hover:bg-slate-50 rounded-xl transition-colors">
                            <X size={18} />
                        </button>
                    </div>
                </div>

                {/* Printable Content */}
                <div className="p-8 print:p-6">
                    {/* Report Header */}
                    <div className="flex items-start justify-between mb-6 pb-5 border-b border-slate-200">
                        <div>
                            <div className="flex items-center gap-2 mb-1">
                                <div className="p-1.5 bg-sky-600 rounded-lg">
                                    <Eye size={18} className="text-white" />
                                </div>
                                <span className="text-xl font-black text-slate-900 tracking-tight">Refracto AI</span>
                            </div>
                            <p className="text-xs text-slate-400 font-medium">AI-powered Ophthalmic Analysis System</p>
                            <p className="text-xs text-slate-400 mt-0.5">Powered by EfficientNet-B3 Multi-Task Learning</p>
                        </div>
                        <div className="text-right">
                            <div className="text-xs font-bold text-slate-500 uppercase tracking-wider mb-1">Report ID</div>
                            <div className="font-mono font-bold text-slate-700">{report.reportId}</div>
                            <div className="text-xs text-slate-400 mt-1 flex items-center gap-1 justify-end">
                                <Calendar size={11} /> {report.date}
                            </div>
                        </div>
                    </div>

                    {/* Patient + Exam Info */}
                    <div className="grid grid-cols-2 gap-4 mb-6">
                        <div className="p-4 bg-slate-50 rounded-2xl border border-slate-100">
                            <div className="flex items-center gap-2 mb-2">
                                <User size={14} className="text-slate-500" />
                                <span className="text-xs font-bold text-slate-500 uppercase tracking-wider">Patient</span>
                            </div>
                            <div className="font-bold text-slate-800">{report.patientName || 'Anonymous'}</div>
                            {report.patientId && <div className="text-xs text-slate-500 mt-0.5">ID: {report.patientId}</div>}
                        </div>
                        <div className="p-4 bg-slate-50 rounded-2xl border border-slate-100">
                            <div className="flex items-center gap-2 mb-2">
                                <Hospital size={14} className="text-slate-500" />
                                <span className="text-xs font-bold text-slate-500 uppercase tracking-wider">Exam Details</span>
                            </div>
                            <div className="font-bold text-slate-800">{report.examType}</div>
                            <div className="text-xs text-slate-500 mt-0.5">
                                AI Confidence: <span className={`font-semibold ${report.confidence >= 90 ? 'text-green-600' : report.confidence >= 75 ? 'text-amber-600' : 'text-red-600'}`}>{report.confidence.toFixed(1)}%</span>
                            </div>
                        </div>
                    </div>

                    {/* Urgency Banner */}
                    {isUrgent && (
                        <div className="mb-5 p-4 bg-red-50 border border-red-200 rounded-2xl flex gap-3">
                            <ShieldAlert size={20} className="text-red-600 flex-shrink-0 mt-0.5" />
                            <div>
                                <div className="font-bold text-red-800 text-sm">Urgent Clinical Attention Required</div>
                                <p className="text-xs text-red-700 mt-0.5">Significant pathology detected. Immediate ophthalmology referral is recommended.</p>
                            </div>
                        </div>
                    )}

                    {/* Section: Refractive Error */}
                    <div className="mb-5">
                        <div className="flex items-center gap-2 mb-3">
                            <Eye size={16} className="text-sky-600" />
                            <h3 className="font-bold text-slate-800 text-sm uppercase tracking-wider">Refractive Correction</h3>
                        </div>
                        <div className="grid grid-cols-3 gap-3 mb-3">
                            {[
                                { label: 'Sphere (SPH)', value: `${report.sphere >= 0 ? '+' : ''}${report.sphere.toFixed(2)}`, unit: 'D', bg: 'bg-sky-50 border-sky-100', text: 'text-sky-700' },
                                { label: 'Cylinder (CYL)', value: `${report.cylinder >= 0 ? '+' : ''}${report.cylinder.toFixed(2)}`, unit: 'D', bg: 'bg-cyan-50 border-cyan-100', text: 'text-cyan-700' },
                                { label: 'Axis', value: `${Math.round(report.axis)}°`, unit: '', bg: 'bg-indigo-50 border-indigo-100', text: 'text-indigo-700' },
                            ].map(({ label, value, unit, bg, text }) => (
                                <div key={label} className={`${bg} border rounded-xl p-3 text-center`}>
                                    <div className={`text-xl font-bold ${text}`}>{value}</div>
                                    {unit && <div className="text-xs text-slate-400">{unit}</div>}
                                    <div className="text-xs text-slate-600 mt-1">{label}</div>
                                </div>
                            ))}
                        </div>
                        <div className={`border rounded-xl p-3 text-sm ${myopia.bg}`}>
                            <span className={`font-bold ${myopia.color}`}>Classification: {myopia.label}</span>
                        </div>
                    </div>

                    {/* Section: Pathology */}
                    <div className="mb-5">
                        <div className="flex items-center gap-2 mb-3">
                            <Activity size={16} className="text-violet-600" />
                            <h3 className="font-bold text-slate-800 text-sm uppercase tracking-wider">Pathology Screening</h3>
                        </div>
                        <div className="space-y-3">
                            {/* DR */}
                            <div className="p-4 bg-white border border-slate-200 rounded-xl">
                                <div className="flex items-center justify-between mb-2">
                                    <div className="flex items-center gap-2">
                                        <FlaskConical size={15} className="text-amber-600" />
                                        <span className="font-semibold text-sm text-slate-800">Diabetic Retinopathy</span>
                                    </div>
                                    <span className={`text-xs font-bold border px-2.5 py-0.5 rounded-full ${getStatusBadge(report.drStatus)}`}>{report.drStatus}</span>
                                </div>
                                <div className="flex items-center justify-between text-sm mb-2">
                                    <span className={`font-bold ${drColor}`}>{drLabel}</span>
                                    <span className="text-slate-500 text-xs">Grade {report.drGrade} of 4</span>
                                </div>
                                <div className="w-full h-2 bg-slate-100 rounded-full overflow-hidden">
                                    <div className={`h-full rounded-full ${report.drStatus === 'Healthy' ? 'bg-green-500' : report.drStatus === 'Warning' ? 'bg-amber-500' : 'bg-red-500'}`} style={{ width: `${report.drScore}%` }} />
                                </div>
                                <div className="text-xs text-slate-400 text-right mt-1">{report.drScore}/100</div>
                            </div>

                            {/* Glaucoma */}
                            <div className="p-4 bg-white border border-slate-200 rounded-xl">
                                <div className="flex items-center justify-between mb-2">
                                    <div className="flex items-center gap-2">
                                        <Target size={15} className="text-purple-600" />
                                        <span className="font-semibold text-sm text-slate-800">Glaucoma Risk</span>
                                    </div>
                                    <span className={`text-xs font-bold border px-2.5 py-0.5 rounded-full ${getStatusBadge(report.glaucomaStatus)}`}>{report.glaucomaStatus}</span>
                                </div>
                                <div className="w-full h-2 bg-slate-100 rounded-full overflow-hidden mb-1">
                                    <div className={`h-full rounded-full ${report.glaucomaStatus === 'Healthy' ? 'bg-green-500' : report.glaucomaStatus === 'Warning' ? 'bg-amber-500' : 'bg-red-500'}`} style={{ width: `${report.glaucomaScore}%` }} />
                                </div>
                                <div className="text-xs text-slate-400 text-right">{report.glaucomaScore}/100 risk score</div>
                            </div>
                        </div>
                    </div>

                    {/* Section: AI Reasoning */}
                    <div className="mb-5">
                        <div className="flex items-center gap-2 mb-3">
                            <Brain size={16} className="text-indigo-600" />
                            <h3 className="font-bold text-slate-800 text-sm uppercase tracking-wider">AI Clinical Reasoning</h3>
                        </div>
                        <div className="space-y-2">
                            {report.reasoning.map((r, i) => (
                                <div key={i} className="flex gap-2 p-3 bg-indigo-50 border border-indigo-100 rounded-xl text-sm text-slate-700">
                                    <span className="text-indigo-500 font-bold mt-0.5">{i + 1}.</span>
                                    <span>{r}</span>
                                </div>
                            ))}
                        </div>
                    </div>

                    {/* Section: Recommendations */}
                    <div className="mb-5">
                        <div className="flex items-center gap-2 mb-3">
                            <ClipboardList size={16} className="text-emerald-600" />
                            <h3 className="font-bold text-slate-800 text-sm uppercase tracking-wider">Recommendations</h3>
                        </div>
                        <div className="space-y-2">
                            <div className="flex gap-2 p-3 bg-sky-50 border border-sky-100 rounded-xl text-sm">
                                <Glasses size={15} className="text-sky-600 flex-shrink-0 mt-0.5" />
                                <div><span className="font-semibold text-sky-800">Lens Recommendation: </span><span className="text-slate-700">{lensRec}</span></div>
                            </div>
                            <div className={`flex gap-2 p-3 rounded-xl text-sm border ${isUrgent ? 'bg-red-50 border-red-200' : 'bg-green-50 border-green-200'}`}>
                                <TrendingUp size={15} className={`${isUrgent ? 'text-red-600' : 'text-green-600'} flex-shrink-0 mt-0.5`} />
                                <div><span className="font-semibold text-slate-800">Follow-up: </span><span className="text-slate-700">{followUp}</span></div>
                            </div>
                        </div>
                    </div>

                    {/* Disclaimer */}
                    <div className="p-4 bg-amber-50 border border-amber-200 rounded-2xl flex gap-3">
                        <AlertTriangle size={16} className="text-amber-500 flex-shrink-0 mt-0.5" />
                        <p className="text-xs text-amber-700 leading-relaxed">
                            <strong>Medical Disclaimer:</strong> This report is generated by an AI system and is intended to assist — not replace — clinical diagnosis. All findings require verification by a qualified ophthalmologist before treatment decisions are made.
                        </p>
                    </div>
                </div>
            </div>
        </div>
    )
}

// ─── Report Card ──────────────────────────────────────────────────────────────
function ReportCard({ report, onView }: { report: ReportData; onView: (r: ReportData) => void }) {
    const isUrgent = report.drGrade >= 3 || report.glaucomaScore >= 70
    const isWarning = !isUrgent && (report.drGrade >= 2 || report.glaucomaScore >= 50)
    return (
        <div className={`bg-white rounded-2xl border p-5 hover:shadow-md transition-all cursor-pointer group ${isUrgent ? 'border-red-200 hover:border-red-300' : isWarning ? 'border-amber-200 hover:border-amber-300' : 'border-slate-200 hover:border-slate-300'}`}
            onClick={() => onView(report)}>
            <div className="flex items-start justify-between mb-3">
                <div>
                    <div className="flex items-center gap-2 mb-0.5">
                        <span className="font-mono text-xs text-slate-400">{report.reportId}</span>
                        {isUrgent && <span className="text-xs font-bold text-red-600 bg-red-50 border border-red-200 px-2 py-0.5 rounded-full">⚡ Urgent</span>}
                        {isWarning && <span className="text-xs font-bold text-amber-600 bg-amber-50 border border-amber-200 px-2 py-0.5 rounded-full">⚠ Review</span>}
                    </div>
                    <div className="font-bold text-slate-800">{report.patientName || 'Anonymous'}</div>
                    <div className="text-xs text-slate-500 flex items-center gap-1.5 mt-0.5">
                        <Calendar size={11} /> {report.date}
                        <span className="text-slate-300">·</span>
                        <span>{report.examType}</span>
                    </div>
                </div>
                <div className="text-right">
                    <div className={`text-sm font-bold ${report.confidence >= 90 ? 'text-green-600' : report.confidence >= 75 ? 'text-amber-600' : 'text-red-600'}`}>
                        {report.confidence.toFixed(1)}%
                    </div>
                    <div className="text-xs text-slate-400">confidence</div>
                </div>
            </div>

            {/* Quick stats */}
            <div className="grid grid-cols-3 gap-2 mb-3">
                <div className="text-center p-2 bg-slate-50 rounded-xl">
                    <div className="text-sm font-bold text-sky-700">{report.sphere >= 0 ? '+' : ''}{report.sphere.toFixed(2)}</div>
                    <div className="text-xs text-slate-400">SPH</div>
                </div>
                <div className={`text-center p-2 rounded-xl ${getStatusBadge(report.drStatus)}`}>
                    <div className="text-sm font-bold">{DR_LABELS[Math.min(report.drGrade, 4)]}</div>
                    <div className="text-xs opacity-75">DR Grade</div>
                </div>
                <div className={`text-center p-2 rounded-xl ${getStatusBadge(report.glaucomaStatus)}`}>
                    <div className="text-sm font-bold">{report.glaucomaScore}%</div>
                    <div className="text-xs opacity-75">Glaucoma</div>
                </div>
            </div>

            <div className="flex items-center justify-between">
                <div className="text-xs text-slate-500">{report.reasoning.length} AI findings</div>
                <span className="text-xs font-semibold text-indigo-600 group-hover:text-indigo-700 flex items-center gap-1">
                    View Full Report <span className="group-hover:translate-x-1 transition-transform inline-block">→</span>
                </span>
            </div>
        </div>
    )
}

// ─── Main Page ────────────────────────────────────────────────────────────────
export default function ReportsPage() {
    const [selectedReport, setSelectedReport] = useState<ReportData | null>(null)
    const [filter, setFilter] = useState<'all' | 'urgent' | 'warning' | 'healthy'>('all')
    const [search, setSearch] = useState('')

    const filtered = DEMO_REPORTS.filter(r => {
        const matchesSearch = !search || r.patientName?.toLowerCase().includes(search.toLowerCase()) || r.reportId.toLowerCase().includes(search.toLowerCase())
        const isUrgent = r.drGrade >= 3 || r.glaucomaScore >= 70
        const isWarning = !isUrgent && (r.drGrade >= 2 || r.glaucomaScore >= 50)
        const isHealthy = !isUrgent && !isWarning
        if (filter === 'urgent') return matchesSearch && isUrgent
        if (filter === 'warning') return matchesSearch && isWarning
        if (filter === 'healthy') return matchesSearch && isHealthy
        return matchesSearch
    })

    const urgentCount = DEMO_REPORTS.filter(r => r.drGrade >= 3 || r.glaucomaScore >= 70).length
    const warningCount = DEMO_REPORTS.filter(r => {
        const isU = r.drGrade >= 3 || r.glaucomaScore >= 70
        return !isU && (r.drGrade >= 2 || r.glaucomaScore >= 50)
    }).length

    return (
        <div className="max-w-5xl mx-auto">
            {selectedReport && <PrintableReport report={selectedReport} onClose={() => setSelectedReport(null)} />}

            {/* Page Header */}
            <div className="flex items-center justify-between mb-6">
                <div>
                    <h1 className="text-2xl font-black text-slate-900 flex items-center gap-3">
                        <div className="p-2 bg-gradient-to-br from-sky-500 to-indigo-600 rounded-xl shadow-md">
                            <FileText size={22} className="text-white" />
                        </div>
                        Clinical Reports
                    </h1>
                    <p className="text-sm text-slate-500 mt-1">AI-generated ophthalmic analysis reports — printable & exportable</p>
                </div>
                <button
                    onClick={() => window.print()}
                    className="flex items-center gap-2 px-4 py-2.5 bg-slate-800 text-white rounded-xl text-sm font-semibold hover:bg-slate-700 transition-colors shadow-md print:hidden"
                >
                    <Printer size={16} /> Print All
                </button>
            </div>

            {/* Stats Row */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mb-6">
                {[
                    { label: 'Total Reports', value: DEMO_REPORTS.length, icon: ClipboardList, color: 'text-slate-700', bg: 'bg-slate-50 border-slate-200' },
                    { label: 'Urgent', value: urgentCount, icon: ShieldAlert, color: 'text-red-700', bg: 'bg-red-50 border-red-200' },
                    { label: 'Needs Review', value: warningCount, icon: AlertTriangle, color: 'text-amber-700', bg: 'bg-amber-50 border-amber-200' },
                    { label: 'Healthy', value: DEMO_REPORTS.length - urgentCount - warningCount, icon: CheckCircle, color: 'text-green-700', bg: 'bg-green-50 border-green-200' },
                ].map(({ label, value, icon: Icon, color, bg }) => (
                    <div key={label} className={`p-4 rounded-2xl border ${bg} flex items-center gap-3`}>
                        <Icon size={20} className={color} />
                        <div>
                            <div className={`text-xl font-black ${color}`}>{value}</div>
                            <div className="text-xs text-slate-500">{label}</div>
                        </div>
                    </div>
                ))}
            </div>

            {/* Search + Filter */}
            <div className="flex flex-col sm:flex-row gap-3 mb-5">
                <input
                    type="text"
                    placeholder="Search by patient name or report ID…"
                    value={search}
                    onChange={e => setSearch(e.target.value)}
                    className="flex-1 px-4 py-2.5 rounded-xl border border-slate-200 text-sm focus:outline-none focus:ring-4 focus:ring-sky-500/10 focus:border-sky-400"
                />
                <div className="flex gap-1 bg-slate-100 p-1 rounded-xl">
                    {(['all', 'urgent', 'warning', 'healthy'] as const).map(f => (
                        <button key={f} onClick={() => setFilter(f)}
                            className={`px-3 py-1.5 text-xs font-semibold rounded-lg capitalize transition-all ${filter === f ? 'bg-white text-slate-800 shadow-sm' : 'text-slate-500 hover:text-slate-700'}`}>
                            {f}
                        </button>
                    ))}
                </div>
            </div>

            {/* Report Cards Grid */}
            {filtered.length > 0 ? (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                    {filtered.map(r => (
                        <ReportCard key={r.reportId} report={r} onView={setSelectedReport} />
                    ))}
                </div>
            ) : (
                <div className="flex flex-col items-center justify-center py-16 text-center border-2 border-dashed border-slate-200 rounded-2xl">
                    <FileText size={48} className="text-slate-300 mb-3" />
                    <h3 className="text-slate-500 font-semibold">No reports found</h3>
                    <p className="text-sm text-slate-400 mt-1">Try adjusting your search or filter</p>
                </div>
            )}

            {/* How reports are generated */}
            <div className="mt-8 p-5 bg-gradient-to-br from-indigo-50 to-sky-50 border border-indigo-100 rounded-2xl">
                <div className="flex items-center gap-2 mb-3">
                    <Sparkles size={16} className="text-indigo-600" />
                    <span className="font-bold text-indigo-800 text-sm">How Refracto AI Reports Are Generated</span>
                </div>
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                    {[
                        { icon: Microscope, title: 'Scan Processing', desc: 'Fundus/OCT images processed by EfficientNet-B3 trained on 100k+ retinal scans' },
                        { icon: Brain, title: 'Multi-Task Inference', desc: 'Simultaneous DR grading, glaucoma risk, and refractive error estimation' },
                        { icon: BarChart3, title: 'XAI Reporting', desc: 'Grad-CAM heatmaps and confidence scores ensure transparent, explainable results' },
                    ].map(({ icon: Icon, title, desc }) => (
                        <div key={title} className="flex gap-3">
                            <div className="p-2 bg-white rounded-xl border border-indigo-100 h-fit">
                                <Icon size={15} className="text-indigo-600" />
                            </div>
                            <div>
                                <div className="text-xs font-bold text-indigo-800">{title}</div>
                                <div className="text-xs text-indigo-700 mt-0.5 leading-relaxed">{desc}</div>
                            </div>
                        </div>
                    ))}
                </div>
            </div>
        </div>
    )
}
