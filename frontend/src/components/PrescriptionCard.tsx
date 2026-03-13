import React, { useState } from 'react'
import { Eye, FileText, AlertTriangle, CheckCircle, Info, Printer, Copy, Check } from 'lucide-react'

export interface PrescriptionData {
    sphere: number
    cylinder: number
    axis: number
    drGrade: number
    glaucomaRisk: number
    patientName?: string
    date?: string
}

function classifyMyopia(sphere: number): { label: string; color: string; description: string } {
    if (sphere <= -9) return { label: 'High Pathological Myopia', color: 'text-red-600 bg-red-50 border-red-200', description: 'Extreme nearsightedness. High risk for myopic maculopathy, retinal detachment, glaucoma.' }
    if (sphere <= -6) return { label: 'High Myopia', color: 'text-orange-600 bg-orange-50 border-orange-200', description: 'Significantly elevated risk of retinal degeneration and glaucoma. Annual retinal exam required.' }
    if (sphere < -3) return { label: 'Moderate Myopia', color: 'text-yellow-600 bg-yellow-50 border-yellow-200', description: 'Moderate nearsightedness. Biennial retinal check recommended.' }
    if (sphere < 0) return { label: 'Mild Myopia', color: 'text-blue-600 bg-blue-50 border-blue-200', description: 'Mild nearsightedness. Routine monitoring.' }
    if (sphere < 0.5) return { label: 'Emmetropia', color: 'text-green-600 bg-green-50 border-green-200', description: 'Normal refraction. No corrective lenses needed for distance vision.' }
    if (sphere < 3) return { label: 'Mild Hyperopia', color: 'text-blue-600 bg-blue-50 border-blue-200', description: 'Mild farsightedness. Reading glasses may help.' }
    return { label: 'Significant Hyperopia', color: 'text-orange-600 bg-orange-50 border-orange-200', description: 'Significant farsightedness. Narrow-angle glaucoma risk — slit-lamp exam recommended.' }
}

function getDRLabel(grade: number): { label: string; color: string; followUp: string } {
    const labels = [
        { label: 'No DR', color: 'text-green-700', followUp: 'Routine follow-up in 12 months.' },
        { label: 'Mild NPDR', color: 'text-yellow-700', followUp: 'Follow-up in 9 months. HbA1c optimisation.' },
        { label: 'Moderate NPDR', color: 'text-orange-700', followUp: 'Ophthalmology referral within 3 months. Fluorescein angiography.' },
        { label: 'Severe NPDR', color: 'text-red-700', followUp: 'Urgent referral within 1 month. Consider pan-retinal photocoagulation.' },
        { label: 'Proliferative DR', color: 'text-red-900', followUp: 'URGENT — Refer within 1 week. Vitreoretinal surgery may be required.' },
    ]
    return labels[Math.min(grade, 4)] ?? labels[0]
}

function formatPrescription(sphere: number, cylinder: number, axis: number): string {
    const sph = `SPH ${sphere >= 0 ? '+' : ''}${sphere.toFixed(2)}`
    const cyl = Math.abs(cylinder) >= 0.25 ? ` CYL ${cylinder >= 0 ? '+' : ''}${cylinder.toFixed(2)} × ${Math.round(axis)}°` : ' SPH only'
    return sph + cyl
}

function getLensRecommendation(sphere: number, cylinder: number): string {
    const absS = Math.abs(sphere)
    const absC = Math.abs(cylinder)
    if (absS <= 1 && absC <= 0.5) return 'Single-vision lenses (low power). Polycarbonate suitable.'
    if (absS <= -6) return 'High-index lenses (1.67 or 1.74) recommended to reduce thickness. Anti-reflective coating essential.'
    if (absC > 2) return 'Toric lenses required for significant astigmatism correction. Precise axis alignment critical.'
    return 'Single-vision or progressive lenses. High-index (1.60+) recommended for comfort.'
}

function getFollowUpInterval(drGrade: number, glaucomaRisk: number, sphere: number): string {
    if (drGrade >= 3 || glaucomaRisk >= 0.7) return '⚡ Urgent — Within 1–4 weeks'
    if (drGrade === 2 || glaucomaRisk >= 0.5 || sphere <= -6) return '🔶 Priority — Within 3 months'
    if (drGrade === 1 || sphere <= -3) return '📅 Routine — 6 months'
    return '📅 Routine — 12 months'
}

export default function PrescriptionCard({ sphere, cylinder, axis, drGrade, glaucomaRisk, patientName, date }: PrescriptionData) {
    const [copied, setCopied] = useState(false)

    const myopia = classifyMyopia(sphere)
    const drInfo = getDRLabel(drGrade)
    const prescriptionText = formatPrescription(sphere, cylinder, axis)
    const lens = getLensRecommendation(sphere, cylinder)
    const followUp = getFollowUpInterval(drGrade, glaucomaRisk, sphere)
    const displayDate = date || new Date().toLocaleDateString('en-IN', { day: '2-digit', month: 'short', year: 'numeric' })

    const fullReport = `REFRACTO AI — CLINICAL PRESCRIPTION
Date: ${displayDate}${patientName ? `\nPatient: ${patientName}` : ''}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
REFRACTIVE ERROR (AI-estimated)
Right Eye (OD): ${prescriptionText}
Left Eye (OS): [Separate image analysis required]

CLASSIFICATION: ${myopia.label}

PATHOLOGY SCREENING
Diabetic Retinopathy: ${drInfo.label} (Grade ${drGrade}/4)
Glaucoma Risk: ${(glaucomaRisk * 100).toFixed(0)}%

LENS RECOMMENDATION
${lens}

FOLLOW-UP
${followUp}

⚠️ This is an AI-assisted report. Clinical verification required before prescribing.`

    const handleCopy = () => {
        navigator.clipboard.writeText(fullReport)
        setCopied(true)
        setTimeout(() => setCopied(false), 2000)
    }

    return (
        <div className="bg-white border border-slate-200 rounded-2xl shadow-sm overflow-hidden">
            {/* Header */}
            <div className="bg-gradient-to-r from-sky-600 to-cyan-500 px-5 py-4">
                <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2 text-white">
                        <FileText size={20} />
                        <h3 className="font-bold text-base">Clinical Prescription</h3>
                    </div>
                    <span className="text-sky-100 text-xs bg-sky-700/40 px-2 py-1 rounded-full">{displayDate}</span>
                </div>
                {patientName && <p className="text-sky-100 text-sm mt-1">Patient: {patientName}</p>}
            </div>

            <div className="p-5 space-y-5">
                {/* Refractive values */}
                <div>
                    <div className="flex items-center gap-2 mb-3">
                        <Eye size={16} className="text-sky-600" />
                        <span className="text-sm font-semibold text-slate-700 uppercase tracking-wide">Refractive Correction (AI Estimate)</span>
                    </div>

                    <div className="grid grid-cols-3 gap-3 mb-3">
                        {[
                            { label: 'Sphere (SPH)', value: `${sphere >= 0 ? '+' : ''}${sphere.toFixed(2)}`, unit: 'D', color: 'sky' },
                            { label: 'Cylinder (CYL)', value: `${cylinder >= 0 ? '+' : ''}${cylinder.toFixed(2)}`, unit: 'D', color: 'cyan' },
                            { label: 'Axis', value: `${Math.round(axis)}`, unit: '°', color: 'indigo' },
                        ].map(({ label, value, unit, color }) => (
                            <div key={label} className={`bg-${color}-50 border border-${color}-200 rounded-xl p-3 text-center`}>
                                <div className={`text-xl font-bold text-${color}-700`}>{value}</div>
                                <div className="text-xs text-slate-500 mt-0.5">{unit}</div>
                                <div className="text-xs text-slate-600 mt-1 leading-tight">{label}</div>
                            </div>
                        ))}
                    </div>

                    {/* Prescription string */}
                    <div className="bg-slate-800 rounded-xl px-4 py-3 font-mono text-white text-sm flex items-center justify-between">
                        <span>OD: {prescriptionText}</span>
                        <span className="text-slate-400 text-xs">OS: Separate scan</span>
                    </div>
                </div>

                {/* Refractive classification */}
                <div className={`border rounded-xl p-3 ${myopia.color}`}>
                    <div className="font-semibold text-sm">{myopia.label}</div>
                    <div className="text-xs mt-0.5 opacity-80">{myopia.description}</div>
                </div>

                {/* Pathology summary */}
                <div>
                    <div className="text-sm font-semibold text-slate-700 mb-2">Pathology Screening</div>
                    <div className="space-y-2">
                        <div className="flex items-center justify-between p-2.5 bg-slate-50 rounded-lg border border-slate-100">
                            <span className="text-sm text-slate-600">Diabetic Retinopathy</span>
                            <span className={`text-sm font-semibold ${drInfo.color}`}>{drInfo.label}</span>
                        </div>
                        <div className="flex items-center justify-between p-2.5 bg-slate-50 rounded-lg border border-slate-100">
                            <span className="text-sm text-slate-600">Glaucoma Risk</span>
                            <span className={`text-sm font-semibold ${glaucomaRisk >= 0.7 ? 'text-red-600' : glaucomaRisk >= 0.4 ? 'text-orange-600' : 'text-green-700'}`}>
                                {(glaucomaRisk * 100).toFixed(0)}% — {glaucomaRisk >= 0.7 ? 'High' : glaucomaRisk >= 0.4 ? 'Moderate' : 'Low'}
                            </span>
                        </div>
                    </div>
                </div>

                {/* Lens recommendation */}
                <div className="flex gap-2 p-3 bg-blue-50 border border-blue-200 rounded-xl">
                    <Info size={16} className="text-blue-600 flex-shrink-0 mt-0.5" />
                    <div>
                        <div className="text-xs font-semibold text-blue-700 mb-0.5">Lens Recommendation</div>
                        <div className="text-xs text-blue-700">{lens}</div>
                    </div>
                </div>

                {/* Follow-up indicator */}
                <div className={`flex gap-2 p-3 rounded-xl border ${drGrade >= 3 || glaucomaRisk >= 0.7
                        ? 'bg-red-50 border-red-200'
                        : drGrade >= 2 || glaucomaRisk >= 0.5
                            ? 'bg-orange-50 border-orange-200'
                            : 'bg-green-50 border-green-200'
                    }`}>
                    {drGrade >= 3 || glaucomaRisk >= 0.7
                        ? <AlertTriangle size={16} className="text-red-600 flex-shrink-0 mt-0.5" />
                        : <CheckCircle size={16} className="text-green-600 flex-shrink-0 mt-0.5" />
                    }
                    <div>
                        <div className="text-xs font-semibold text-slate-700 mb-0.5">Recommended Follow-up</div>
                        <div className="text-xs text-slate-600">{followUp}</div>
                        <div className="text-xs text-slate-500 mt-1">{drInfo.followUp}</div>
                    </div>
                </div>

                {/* AI Disclaimer */}
                <div className="flex gap-2 p-3 bg-amber-50 border border-amber-200 rounded-xl">
                    <AlertTriangle size={14} className="text-amber-500 flex-shrink-0 mt-0.5" />
                    <p className="text-xs text-amber-700">AI-assisted estimate. Requires clinical verification and objective refraction before dispensing.</p>
                </div>

                {/* Action buttons */}
                <div className="flex gap-2 pt-1">
                    <button
                        onClick={handleCopy}
                        className="flex-1 flex items-center justify-center gap-2 py-2.5 border border-slate-200 text-slate-600 rounded-xl text-sm font-medium hover:bg-slate-50 transition-colors"
                    >
                        {copied ? <Check size={16} className="text-green-600" /> : <Copy size={16} />}
                        {copied ? 'Copied!' : 'Copy Report'}
                    </button>
                    <button
                        onClick={() => window.print()}
                        className="flex-1 flex items-center justify-center gap-2 py-2.5 bg-sky-600 hover:bg-sky-700 text-white rounded-xl text-sm font-medium transition-colors"
                    >
                        <Printer size={16} />
                        Print
                    </button>
                </div>
            </div>
        </div>
    )
}
