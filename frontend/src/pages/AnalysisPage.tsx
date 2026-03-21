import React, { useState, useCallback, useRef } from 'react'
import {
    Upload, Loader2, Brain, Eye, Activity, AlertTriangle,
    CheckCircle, FileText, Zap, ChevronDown, ChevronUp,
    X, Sparkles, Printer, Glasses, Info, ShieldAlert, Download,
    TrendingUp, Target, Microscope, FlaskConical, HeartPulse, BookOpen,
    BarChart3, Layers, CircleAlert, LucideIcon
} from 'lucide-react'
import { useSearchParams } from 'react-router-dom'
import { mlService, analyzeScan, AnalysisResult } from '../services/api'
import PrescriptionCard from '../components/PrescriptionCard'
import { generateDicomPreview } from '../utils/dicomParser'

// ─── Eye Condition Knowledge Base ────────────────────────────────────────────
const CONDITIONS = {
    diabeticRetinopathy: {
        title: 'Diabetic Retinopathy (DR)',
        icon: FlaskConical,
        color: 'amber',
        whatIsIt: 'Diabetic retinopathy is a diabetes complication that affects the eyes. It\'s caused by damage to the blood vessels of the light-sensitive tissue at the back of the eye (retina).',
        whyItHappens: 'Chronically high blood sugar levels damage the tiny blood vessels in the retina, causing them to leak fluid, swell, or grow abnormally. Over time this leads to vision loss if untreated.',
        stages: [
            { grade: 0, label: 'No DR', color: 'green', desc: 'No signs of diabetic retinopathy detected. Continue routine annual eye exams.' },
            { grade: 1, label: 'Mild NPDR', color: 'yellow', desc: 'Small areas of balloon-like swelling in retinal blood vessels (microaneurysms). Annual monitoring required.' },
            { grade: 2, label: 'Moderate NPDR', color: 'orange', desc: 'More blocked blood vessels — some nutrient supply disruption. Follow-up in 3–6 months.' },
            { grade: 3, label: 'Severe NPDR', color: 'red', desc: 'Many blocked vessels deprive retina of blood supply. Body tries to grow new blood vessels. Urgent referral needed.' },
            { grade: 4, label: 'Proliferative DR', color: 'rose', desc: 'Advanced stage — new fragile blood vessels grow (neovascularisation), may bleed into vitreous. Immediate treatment required.' },
        ],
        riskFactors: ['Duration of diabetes', 'Poor blood sugar control (high HbA1c)', 'High blood pressure', 'High cholesterol', 'Pregnancy', 'Tobacco use'],
        whatItMeans: 'DR is the leading cause of blindness in working-age adults worldwide. Early detection and treatment can prevent up to 95% of vision loss.',
    },
    glaucoma: {
        title: 'Glaucoma',
        icon: Target,
        color: 'purple',
        whatIsIt: 'Glaucoma is a group of eye conditions that damage the optic nerve, which is critical for good vision. This damage is often caused by abnormally high pressure in the eye (intraocular pressure, IOP).',
        whyItHappens: 'The eye continuously produces fluid (aqueous humour). In glaucoma, this fluid doesn\'t drain properly, increasing pressure that compresses and damages the optic nerve fibres — causing irreversible blind spots.',
        riskFactors: ['Age over 60', 'Family history of glaucoma', 'Elevated IOP', 'Thin central corneas', 'High myopia (>–6D)', 'African or Hispanic descent', 'Diabetes and hypertension'],
        whatItMeans: 'Glaucoma is often called the "silent thief of sight" — it has no symptoms in early stages. By the time vision loss is noticed, permanent damage has occurred. The AI analyses the optic disc cup-to-disc ratio and nerve fibre layers.',
    },
    refractiveError: {
        title: 'Refractive Error',
        icon: Glasses,
        color: 'sky',
        whatIsIt: 'A refractive error occurs when the shape of the eye prevents light from focusing directly on the retina, causing blurred vision.',
        types: [
            { name: 'Myopia (Short-sightedness)', trigger: (s: number) => s < -0.5, desc: 'Eyeball is too long or cornea too curved. Light focuses in front of the retina. Distant objects appear blurry.' },
            { name: 'Hyperopia (Long-sightedness)', trigger: (s: number) => s > 0.5, desc: 'Eyeball is too short or cornea too flat. Light focuses behind the retina. Close objects appear blurry.' },
            { name: 'Emmetropia (Normal)', trigger: (s: number) => s >= -0.5 && s <= 0.5, desc: 'Normal refraction. Light focuses directly on the retina. Clear vision at all distances.' },
            { name: 'Astigmatism', trigger: (_: number, c: number) => Math.abs(c) >= 0.75, desc: 'Irregular curvature of cornea or lens causes distorted vision at all distances.' },
        ],
        whyItHappens: 'Influenced by genetics and environmental factors during childhood development. The eyeball grows too long (myopia) or too short (hyperopia). Astigmatism is caused by an irregular corneal or lens shape.',
    },
}

// ─── Spectacle Recommendation Logic ──────────────────────────────────────────
function getSpectacleRecommendation(sphere: number, cylinder: number) {
    const absS = Math.abs(sphere)
    const absC = Math.abs(cylinder)
    const needsCorrection = absS >= 0.5 || absC >= 0.75
    const isHighPower = absS >= 6 || absC >= 3
    const isMild = absS < 1.5 && absC < 1

    if (!needsCorrection) {
        return {
            recommended: false,
            type: 'None Required',
            icon: '✅',
            description: 'Vision correction is not required. Your refractive error is within normal limits.',
            lensType: null,
            contactLensSuitable: false,
            urgency: 'routine',
        }
    }
    return {
        recommended: true,
        type: sphere < -0.5 ? 'Distance Spectacles' : sphere > 0.5 ? 'Reading/Near Spectacles' : 'Astigmatic Correction',
        icon: '👓',
        description: isMild
            ? 'Mild correction needed. Spectacles are recommended for prolonged screen use or driving.'
            : isHighPower
            ? 'Significant refractive error detected. High-index lenses (1.67–1.74) are essential for comfort and reduced thickness. Daily use strongly recommended.'
            : 'Correction is recommended for daily activities. Regular glasses advised.',
        lensType: absC > 2
            ? 'Toric lenses (corrects astigmatism) — precise axis alignment required'
            : isHighPower
            ? 'High-index lenses (1.67 or 1.74) — thinner and lighter'
            : 'Standard single-vision lenses (1.50 or 1.60 index)',
        contactLensSuitable: absS <= 10 && absC <= 4,
        urgency: absS >= 6 ? 'priority' : 'routine',
    }
}

// ─── Enhanced Grad-CAM Modal ──────────────────────────────────────────────────
const ANATOMICAL_REGIONS = [
    { name: 'Optic Disc', desc: 'The origin of the optic nerve. Enlargement of the central cup (cup-to-disc ratio) is a key indicator of glaucoma.', relevance: 'Glaucoma risk assessment' },
    { name: 'Macula / Fovea', desc: 'The central area of the retina responsible for sharp, detailed central vision. Macular degeneration or oedema appears here.', relevance: 'DR macular oedema, AMD' },
    { name: 'Blood Vessels (Arteries/Veins)', desc: 'Retinal blood vessels carry oxygen and nutrients. Abnormalities include microaneurysms, haemorrhages, and neovascularisation in DR.', relevance: 'Diabetic Retinopathy staging' },
    { name: 'Nerve Fibre Layer (NFL)', desc: 'The innermost retinal layer containing axons from ganglion cells. Thinning indicates glaucoma progression.', relevance: 'Glaucoma progression' },
    { name: 'Peripheral Retina', desc: 'The outer region of the retina. Lattice degeneration or tears are common in high myopia.', relevance: 'Retinal detachment risk in high myopia' },
]

function HeatmapModal({ heatmap, explanation, results, onClose }: {
    heatmap: string
    explanation: string
    results?: AnalysisResult | null
    onClose: () => void
}) {
    const [activeRegion, setActiveRegion] = useState<number | null>(null)
    const [activeTab, setActiveTab] = useState<'visual' | 'regions' | 'clinical'>('visual')

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-md" onClick={onClose}>
            <div className="bg-white rounded-3xl shadow-2xl max-w-3xl w-full max-h-[92vh] overflow-y-auto" onClick={e => e.stopPropagation()}>
                {/* Header */}
                <div className="bg-gradient-to-r from-indigo-600 via-violet-600 to-purple-600 px-6 py-5 flex items-center justify-between rounded-t-3xl sticky top-0 z-10">
                    <div className="flex items-center gap-3 text-white">
                        <div className="p-2 bg-white/20 rounded-xl backdrop-blur-sm">
                            <Brain size={22} />
                        </div>
                        <div>
                            <div className="font-bold text-lg">Grad-CAM XAI Analysis</div>
                            <div className="text-indigo-200 text-xs font-medium">Gradient-weighted Class Activation Mapping</div>
                        </div>
                    </div>
                    <button onClick={onClose} className="text-white/70 hover:text-white bg-white/10 hover:bg-white/20 p-2 rounded-xl transition-colors">
                        <X size={20} />
                    </button>
                </div>

                {/* What is Grad-CAM banner */}
                <div className="mx-6 mt-5 p-4 bg-indigo-50 border border-indigo-100 rounded-2xl">
                    <div className="flex gap-3">
                        <Info size={18} className="text-indigo-600 flex-shrink-0 mt-0.5" />
                        <div>
                            <div className="text-sm font-bold text-indigo-800 mb-1">What is Grad-CAM?</div>
                            <p className="text-xs text-indigo-700 leading-relaxed">
                                Gradient-weighted Class Activation Mapping (<strong>Grad-CAM</strong>) visualises which regions of the retinal scan the AI model focused on when making its predictions. <strong>Red/warm areas</strong> had the highest influence on the diagnosis, while <strong>blue/cool areas</strong> had minimal impact — making the AI's decision transparent.
                            </p>
                        </div>
                    </div>
                </div>

                {/* Tabs */}
                <div className="flex gap-1 mx-6 mt-4 bg-slate-100 p-1 rounded-2xl">
                    {([['visual', 'Heatmap Visual'], ['regions', 'Anatomical Regions'], ['clinical', 'Clinical Significance']] as const).map(([tab, label]) => (
                        <button
                            key={tab}
                            onClick={() => setActiveTab(tab)}
                            className={`flex-1 py-2 text-sm font-semibold rounded-xl transition-all ${activeTab === tab ? 'bg-white text-indigo-700 shadow-sm' : 'text-slate-500 hover:text-slate-700'}`}
                        >
                            {label}
                        </button>
                    ))}
                </div>

                <div className="p-6">
                    {/* Visual Tab */}
                    {activeTab === 'visual' && (
                        <div className="space-y-5">
                            <div className="relative">
                                <img src={heatmap} alt="Grad-CAM heatmap" className="w-full rounded-2xl border border-slate-200 shadow-md" />
                                <div className="absolute top-3 right-3 bg-black/60 backdrop-blur-sm text-white text-xs px-3 py-1.5 rounded-full font-medium">
                                    AI Attention Map
                                </div>
                            </div>

                            {/* Color Legend */}
                            <div className="bg-slate-50 rounded-2xl p-4 border border-slate-200">
                                <div className="text-xs font-bold text-slate-600 uppercase tracking-wider mb-3">Activation Intensity Scale</div>
                                <div className="flex items-center gap-2 mb-3">
                                    <div className="h-4 flex-1 rounded-full" style={{ background: 'linear-gradient(to right, #3b82f6, #22d3ee, #84cc16, #fbbf24, #f97316, #ef4444)' }} />
                                </div>
                                <div className="flex justify-between text-xs text-slate-500 font-medium">
                                    <span className="text-blue-600">◀ Low (not relevant)</span>
                                    <span className="text-slate-600">Medium</span>
                                    <span className="text-red-600">High (critical region) ▶</span>
                                </div>
                                <div className="grid grid-cols-3 gap-2 mt-3">
                                    {[
                                        { color: 'bg-red-500', label: 'Critical', desc: 'Primary diagnostic region — highest influence on diagnosis' },
                                        { color: 'bg-yellow-400', label: 'Significant', desc: 'Secondary region — moderately influential' },
                                        { color: 'bg-blue-500', label: 'Background', desc: 'Low relevance — minimal impact on prediction' },
                                    ].map(({ color, label, desc }) => (
                                        <div key={label} className="flex flex-col gap-1.5 p-2.5 bg-white rounded-xl border border-slate-100">
                                            <div className="flex items-center gap-1.5">
                                                <div className={`w-3 h-3 rounded-full ${color}`} />
                                                <span className="text-xs font-bold text-slate-700">{label}</span>
                                            </div>
                                            <span className="text-xs text-slate-500 leading-tight">{desc}</span>
                                        </div>
                                    ))}
                                </div>
                            </div>

                            <div className="p-4 bg-violet-50 border border-violet-100 rounded-2xl">
                                <div className="text-xs font-bold text-violet-700 uppercase tracking-wider mb-2 flex items-center gap-1.5">
                                    <Brain size={13} /> AI Explanation
                                </div>
                                <p className="text-sm text-slate-700 leading-relaxed">{explanation}</p>
                            </div>
                        </div>
                    )}

                    {/* Anatomical Regions Tab */}
                    {activeTab === 'regions' && (
                        <div className="space-y-3">
                            <p className="text-sm text-slate-500 mb-4">The AI examines multiple retinal structures. Select a region to understand its clinical significance.</p>
                            {ANATOMICAL_REGIONS.map((region, i) => (
                                <button
                                    key={i}
                                    onClick={() => setActiveRegion(activeRegion === i ? null : i)}
                                    className={`w-full text-left p-4 rounded-2xl border transition-all ${activeRegion === i ? 'bg-indigo-50 border-indigo-300 shadow-sm' : 'bg-slate-50 border-slate-200 hover:border-indigo-200 hover:bg-indigo-50/30'}`}
                                >
                                    <div className="flex items-center justify-between">
                                        <div className="flex items-center gap-2">
                                            <div className={`w-2 h-2 rounded-full ${activeRegion === i ? 'bg-indigo-500' : 'bg-slate-400'}`} />
                                            <span className="font-semibold text-sm text-slate-800">{region.name}</span>
                                        </div>
                                        <span className="text-xs bg-indigo-100 text-indigo-700 px-2 py-0.5 rounded-full font-medium">{region.relevance}</span>
                                    </div>
                                    {activeRegion === i && (
                                        <p className="mt-3 text-sm text-slate-600 leading-relaxed pl-4 border-l-2 border-indigo-300">{region.desc}</p>
                                    )}
                                </button>
                            ))}
                        </div>
                    )}

                    {/* Clinical Significance Tab */}
                    {activeTab === 'clinical' && (
                        <div className="space-y-4">
                            <div className="p-4 bg-amber-50 border border-amber-100 rounded-2xl">
                                <div className="flex gap-2 mb-2">
                                    <CircleAlert size={16} className="text-amber-600 flex-shrink-0 mt-0.5" />
                                    <span className="text-sm font-bold text-amber-800">Important Disclaimer</span>
                                </div>
                                <p className="text-xs text-amber-700 leading-relaxed">
                                    Grad-CAM is an explainability tool — it shows where the model looks, not a clinical diagnosis. The highlighted regions should be interpreted by a qualified ophthalmologist alongside the full clinical context.
                                </p>
                            </div>

                            {results && (
                                <div className="space-y-3">
                                    <h4 className="text-sm font-bold text-slate-700">What the AI Detected in This Scan:</h4>
                                    <div className="space-y-2">
                                        {[
                                            {
                                                condition: 'Diabetic Retinopathy',
                                                score: results.pathology.diabetic_retinopathy.score,
                                                status: results.pathology.diabetic_retinopathy.status,
                                                focusArea: 'Blood vessels, microaneurysms, haemorrhages',
                                            },
                                            {
                                                condition: 'Glaucoma Risk',
                                                score: results.pathology.glaucoma.score,
                                                status: results.pathology.glaucoma.status,
                                                focusArea: 'Optic disc cup-to-disc ratio, nerve fibre layer',
                                            },
                                        ].map(({ condition, score, status, focusArea }) => (
                                            <div key={condition} className="p-3 bg-white border border-slate-200 rounded-xl">
                                                <div className="flex justify-between mb-1">
                                                    <span className="text-sm font-semibold text-slate-800">{condition}</span>
                                                    <span className={`text-xs font-bold px-2 py-0.5 rounded-full ${status === 'Healthy' ? 'bg-green-100 text-green-700' : status === 'Warning' ? 'bg-amber-100 text-amber-700' : 'bg-red-100 text-red-700'}`}>{status}</span>
                                                </div>
                                                <div className="text-xs text-slate-500 mb-2">Focus region: <span className="text-slate-700 font-medium">{focusArea}</span></div>
                                                <div className="w-full h-1.5 bg-slate-100 rounded-full overflow-hidden">
                                                    <div className={`h-full rounded-full ${status === 'Healthy' ? 'bg-green-500' : status === 'Warning' ? 'bg-amber-500' : 'bg-red-500'}`} style={{ width: `${score}%` }} />
                                                </div>
                                                <div className="text-xs text-slate-400 text-right mt-1">{score.toFixed(0)} / 100</div>
                                            </div>
                                        ))}
                                    </div>
                                </div>
                            )}

                            <div className="p-4 bg-slate-50 border border-slate-200 rounded-2xl">
                                <div className="text-sm font-bold text-slate-700 mb-2">How to Interpret This Report</div>
                                <ul className="space-y-2 text-xs text-slate-600">
                                    <li className="flex gap-2"><span className="text-indigo-500 font-bold mt-0.5">→</span> Red heatmap regions correlate with the model's highest activation for the predicted class</li>
                                    <li className="flex gap-2"><span className="text-indigo-500 font-bold mt-0.5">→</span> The model was trained on thousands of fundus images using EfficientNet-B3 architecture</li>
                                    <li className="flex gap-2"><span className="text-indigo-500 font-bold mt-0.5">→</span> Grad-CAM uses backpropagated gradients to produce a coarse localisation map</li>
                                    <li className="flex gap-2"><span className="text-indigo-500 font-bold mt-0.5">→</span> Clinical verification is mandatory before any treatment decision</li>
                                </ul>
                            </div>
                        </div>
                    )}
                </div>
            </div>
        </div>
    )
}

// ─── Severity badge helpers ───────────────────────────────────────────────────
function getSeverityBadge(status: 'Healthy' | 'Warning' | 'Severe') {
    if (status === 'Healthy') return 'bg-green-100 text-green-700 border-green-200'
    if (status === 'Warning') return 'bg-amber-100 text-amber-700 border-amber-200'
    return 'bg-red-100 text-red-700 border-red-200'
}

function ScoreBar({ score, status }: { score: number; status: 'Healthy' | 'Warning' | 'Severe' }) {
    const color = status === 'Healthy' ? 'bg-green-500' : status === 'Warning' ? 'bg-amber-500' : 'bg-red-500'
    return (
        <div className="w-full h-2 bg-slate-100 rounded-full overflow-hidden">
            <div className={`h-full rounded-full transition-all duration-700 ${color}`} style={{ width: `${score}%` }} />
        </div>
    )
}

// ─── Condition Detail Panel ────────────────────────────────────────────────────
function ConditionExplainer({ title, icon: Icon, color, score, status, grade, children }: {
    title: string; icon: LucideIcon; color: string; score: number; status: string; grade?: number; children: React.ReactNode
}) {
    const [open, setOpen] = useState(false)
    const statusColor = status === 'Healthy' ? 'text-green-700 bg-green-100 border-green-200' : status === 'Warning' ? 'text-amber-700 bg-amber-100 border-amber-200' : 'text-red-700 bg-red-100 border-red-200'
    const barColor = status === 'Healthy' ? 'from-green-400 to-green-600' : status === 'Warning' ? 'from-amber-400 to-amber-600' : 'from-red-400 to-red-600'
    return (
        <div className={`rounded-2xl border overflow-hidden transition-all duration-300 ${open ? 'border-indigo-200 shadow-md' : 'border-slate-200 hover:border-slate-300'} bg-white`}>
            <button onClick={() => setOpen(o => !o)} className="w-full text-left p-5">
                <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                        <div className={`p-2 rounded-xl bg-${color}-50`}>
                            <Icon size={18} className={`text-${color}-600`} />
                        </div>
                        <span className="font-bold text-slate-800">{title}</span>
                    </div>
                    <div className="flex items-center gap-2">
                        <span className={`text-xs font-bold border px-2.5 py-0.5 rounded-full ${statusColor}`}>{status}</span>
                        {open ? <ChevronUp size={16} className="text-slate-400" /> : <ChevronDown size={16} className="text-slate-400" />}
                    </div>
                </div>
                {/* Score bar */}
                <div className="mt-3">
                    <div className="flex justify-between text-xs text-slate-400 mb-1.5">
                        <span>Risk Score</span>
                        <span className="font-semibold text-slate-600">{score.toFixed(0)} / 100</span>
                    </div>
                    <div className="w-full h-2.5 bg-slate-100 rounded-full overflow-hidden">
                        <div className={`h-full rounded-full bg-gradient-to-r ${barColor} transition-all duration-700`} style={{ width: `${score}%` }} />
                    </div>
                </div>
            </button>
            {open && (
                <div className="border-t border-slate-100 px-5 pb-5 pt-4 bg-slate-50/50">
                    {children}
                </div>
            )}
        </div>
    )
}

// ─── Info Subsection ──────────────────────────────────────────────────────────
function InfoSection({ icon: Icon, title, children }: { icon: LucideIcon; title: string; children: React.ReactNode }) {
    return (
        <div className="mb-4">
            <div className="flex items-center gap-1.5 mb-1.5">
                <Icon size={14} className="text-indigo-500" />
                <span className="text-xs font-bold text-slate-600 uppercase tracking-wide">{title}</span>
            </div>
            <div className="text-sm text-slate-600 leading-relaxed pl-5">{children}</div>
        </div>
    )
}

// ─── Main Component ───────────────────────────────────────────────────────────
export default function AnalysisPage() {
    const [searchParams] = useSearchParams()
    const patientId = searchParams.get('patientId') ?? undefined

    const [selectedFile, setSelectedFile] = useState<File | null>(null)
    const [previewUrl, setPreviewUrl] = useState<string | null>(null)
    const [isDragging, setIsDragging] = useState(false)
    const [isAnalyzing, setIsAnalyzing] = useState(false)
    const [results, setResults] = useState<AnalysisResult | null>(null)
    const [error, setError] = useState<string | null>(null)
    const [isGeneratingPreview, setIsGeneratingPreview] = useState(false)

    // Refractive Input State
    const [manualSphere, setManualSphere] = useState<string>('')
    const [manualCylinder, setManualCylinder] = useState<string>('')
    const [manualAxis, setManualAxis] = useState<string>('')

    // XAI / Heatmap state
    const [heatmapData, setHeatmapData] = useState<{ image: string; explanation: string } | null>(null)
    const [isLoadingHeatmap, setIsLoadingHeatmap] = useState(false)
    const [showHeatmap, setShowHeatmap] = useState(false)

    // Results tab
    const [activeTab, setActiveTab] = useState<'overview' | 'conditions' | 'prescription'>('overview')

    const fileInputRef = useRef<HTMLInputElement>(null)

    // ── File handling ────────────────────────────────────────────────────────────
    const handleFiles = useCallback((files: FileList | null) => {
        if (!files || files.length === 0) return
        const file = files[0]
        const isDicom = file.name.toLowerCase().endsWith('.dcm') || file.name.toLowerCase().endsWith('.dicom')
        if (!isDicom && !file.type.startsWith('image/')) {
            setError('Please upload an image file (JPEG, PNG, TIFF, BMP) or a DICOM (.dcm) file.')
            return
        }
        setSelectedFile(file)
        setResults(null)
        setError(null)
        setHeatmapData(null)
        setActiveTab('overview')
        if (!isDicom) {
            const url = URL.createObjectURL(file)
            setPreviewUrl(url)
        } else {
            setIsGeneratingPreview(true)
            generateDicomPreview(file)
                .then(url => setPreviewUrl(url))
                .catch(() => setPreviewUrl(null))
                .finally(() => setIsGeneratingPreview(false))
        }
    }, [])

    const handleDrop = useCallback((e: React.DragEvent) => {
        e.preventDefault()
        setIsDragging(false)
        handleFiles(e.dataTransfer.files)
    }, [handleFiles])

    const clearFile = () => {
        if (previewUrl) URL.revokeObjectURL(previewUrl)
        setSelectedFile(null)
        setPreviewUrl(null)
        setResults(null)
        setError(null)
        setHeatmapData(null)
    }

    // ── Analysis ─────────────────────────────────────────────────────────────────
    const handleAnalyze = async () => {
        if (!selectedFile) return
        setIsAnalyzing(true)
        setError(null)
        setResults(null)
        setHeatmapData(null)
        try {
            const parsedSphere = parseFloat(manualSphere)
            const parsedCylinder = parseFloat(manualCylinder)
            const parsedAxis = parseFloat(manualAxis)
            const manualData = (!isNaN(parsedSphere) && !isNaN(parsedCylinder) && !isNaN(parsedAxis))
                ? { sphere: parsedSphere, cylinder: parsedCylinder, axis: parsedAxis }
                : undefined
            const data = await analyzeScan(selectedFile, patientId, manualData)
            setResults(data)
            setActiveTab('overview')
        } catch (err: any) {
            setError(err.message || 'Analysis failed. Is the ML service running?')
        } finally {
            setIsAnalyzing(false)
        }
    }

    // ── Grad-CAM XAI ─────────────────────────────────────────────────────────────
    const handleExplain = async () => {
        if (!selectedFile) return
        setIsLoadingHeatmap(true)
        try {
            const xaiResult = await mlService.explainPathology(selectedFile)
            setHeatmapData({ image: xaiResult.heatmap_base64, explanation: xaiResult.explanation })
            setShowHeatmap(true)
        } catch {
            setError('Grad-CAM explanation failed. Model may not be loaded yet.')
        } finally {
            setIsLoadingHeatmap(false)
        }
    }

    const isDicomFile = selectedFile?.name.toLowerCase().endsWith('.dcm') || selectedFile?.name.toLowerCase().endsWith('.dicom')

    // ── Derived data for conditions tab ──────────────────────────────────────────
    const drGrade = results ? Math.round(results.pathology.diabetic_retinopathy.score / 25) : 0
    const glaucomaRisk = results ? results.pathology.glaucoma.score / 100 : 0
    const sphere = results?.refraction.sphere ?? 0
    const cylinder = results?.refraction.cylinder ?? 0
    const spectacleRec = results ? getSpectacleRecommendation(sphere, cylinder) : null
    const drInfo = CONDITIONS.diabeticRetinopathy.stages[Math.min(drGrade, 4)]

    return (
        <div className="min-h-[calc(100vh-6rem)] flex flex-col lg:flex-row gap-6 print:block print:w-full">

            {/* ── Left Panel: Upload ─────────────────────────────────────── */}
            <div className="lg:w-[45%] flex flex-col gap-4 print:hidden">
                <div className="flex items-center justify-between">
                    <h2 className="text-xl font-bold text-slate-800 flex items-center gap-2">
                        <Activity size={22} className="text-sky-600" />
                        Scan Analysis
                    </h2>
                    {patientId && (
                        <span className="text-xs text-sky-700 bg-sky-50 border border-sky-200 px-3 py-1 rounded-full font-medium">
                            Patient #{patientId.slice(0, 8)}
                        </span>
                    )}
                </div>

                {/* Drop zone */}
                {!selectedFile ? (
                    <div
                        className={`flex-1 min-h-72 border-2 border-dashed rounded-3xl flex flex-col items-center justify-center gap-5 p-8 text-center
                          transition-all duration-300 cursor-pointer select-none group
                          ${isDragging ? 'border-sky-500 bg-sky-50/80 scale-[1.02] shadow-xl' : 'border-slate-300 bg-slate-50 hover:border-sky-400 hover:bg-sky-50/50 hover:shadow-lg hover:-translate-y-1'}`}
                        onDragOver={e => { e.preventDefault(); setIsDragging(true) }}
                        onDragLeave={() => setIsDragging(false)}
                        onDrop={handleDrop}
                        onClick={() => fileInputRef.current?.click()}
                    >
                        <div className={`p-5 rounded-2xl transition-all duration-300 ${isDragging ? 'bg-sky-200' : 'bg-white shadow-sm group-hover:scale-110 group-hover:bg-sky-100'}`}>
                            <Upload className={`${isDragging ? 'text-sky-700' : 'text-sky-500'}`} size={36} />
                        </div>
                        <div>
                            <p className="text-xl font-bold text-slate-800 mb-2">Drop your medical scan here</p>
                            <p className="text-sm font-medium text-slate-500">Fundus, OCT, or DICOM (.dcm) — or click to browse</p>
                        </div>
                        <div className="flex flex-wrap justify-center gap-2 mt-2">
                            {['JPEG', 'PNG', 'TIFF', 'DICOM'].map(t => (
                                <span key={t} className="text-xs bg-white border border-slate-200 text-slate-600 font-semibold px-3 py-1.5 rounded-full shadow-sm">{t}</span>
                            ))}
                        </div>
                    </div>
                ) : (
                    <div className="flex flex-col gap-4">
                        {/* Image preview */}
                        <div className="relative bg-slate-900 rounded-2xl overflow-hidden aspect-square w-full flex items-center justify-center">
                            {isGeneratingPreview ? (
                                <div className="flex flex-col items-center gap-3 text-slate-400">
                                    <Loader2 size={48} className="animate-spin text-sky-500" />
                                    <span className="text-sm">Generating DICOM preview…</span>
                                </div>
                            ) : previewUrl ? (
                                <img src={previewUrl} alt="Selected scan" className="w-full h-full object-contain" />
                            ) : (
                                <div className="flex flex-col items-center gap-3 text-slate-400">
                                    <FileText size={48} />
                                    <span className="text-sm">DICOM file — {(selectedFile.size / 1024 / 1024).toFixed(2)} MB</span>
                                </div>
                            )}
                            <button onClick={clearFile} className="absolute top-3 right-3 bg-white/90 text-slate-600 hover:bg-white rounded-full p-1.5 shadow-md">
                                <X size={16} />
                            </button>
                            <div className="absolute bottom-3 left-3 bg-black/50 backdrop-blur-sm text-white text-xs px-3 py-1.5 rounded-full">
                                {isDicomFile ? '🩻 DICOM' : '🖼️ Image'} · {selectedFile.name.length > 28 ? selectedFile.name.slice(0, 25) + '…' : selectedFile.name}
                            </div>
                        </div>

                        {/* Refractive Data Inputs */}
                        <div className="bg-slate-50/80 border border-slate-200/80 rounded-2xl p-5 flex flex-col gap-3">
                            <div className="flex items-center gap-2">
                                <Glasses size={15} className="text-sky-600" />
                                <span className="text-sm font-bold text-slate-700">Manual Refractive Data <span className="text-slate-400 font-normal">(optional)</span></span>
                            </div>
                            <div className="flex gap-3">
                                <div className="flex-1 flex flex-col gap-1">
                                    <label className="text-xs text-slate-500 font-medium">Sphere (D)</label>
                                    <input type="number" step="0.25" placeholder="e.g. -2.50" value={manualSphere} onChange={e => setManualSphere(e.target.value)} className="px-3 py-2.5 text-sm font-medium rounded-xl border border-slate-200 focus:outline-none focus:ring-4 focus:ring-sky-500/10 focus:border-sky-500 transition-all" />
                                </div>
                                <div className="flex-1 flex flex-col gap-1">
                                    <label className="text-xs text-slate-500 font-medium">Cylinder (D)</label>
                                    <input type="number" step="0.25" placeholder="e.g. -0.75" value={manualCylinder} onChange={e => setManualCylinder(e.target.value)} className="px-3 py-2.5 text-sm font-medium rounded-xl border border-slate-200 focus:outline-none focus:ring-4 focus:ring-sky-500/10 focus:border-sky-500 transition-all" />
                                </div>
                                <div className="flex-1 flex flex-col gap-1">
                                    <label className="text-xs text-slate-500 font-medium">Axis (°)</label>
                                    <input type="number" step="1" placeholder="e.g. 90" value={manualAxis} onChange={e => setManualAxis(e.target.value)} className="px-3 py-2.5 text-sm font-medium rounded-xl border border-slate-200 focus:outline-none focus:ring-4 focus:ring-sky-500/10 focus:border-sky-500 transition-all" />
                                </div>
                            </div>
                        </div>

                        {/* Action buttons */}
                        <div className="flex gap-3">
                            <button
                                onClick={handleAnalyze}
                                disabled={isAnalyzing}
                                className="flex-1 bg-sky-600 hover:bg-sky-700 disabled:opacity-60 text-white font-bold py-3.5 rounded-2xl flex items-center justify-center gap-2 shadow-lg shadow-sky-600/20 active:scale-[0.98] transition-all hover:-translate-y-0.5"
                            >
                                {isAnalyzing ? <Loader2 size={20} className="animate-spin" /> : <Sparkles size={20} />}
                                {isAnalyzing ? 'Analysing…' : 'Run AI Analysis'}
                            </button>
                            {results && (
                                <button
                                    onClick={handleExplain}
                                    disabled={isLoadingHeatmap}
                                    className="flex items-center gap-2 px-5 py-3.5 border border-indigo-200 text-indigo-700 hover:bg-indigo-50 disabled:opacity-60 rounded-2xl font-bold text-sm transition-all shadow-sm hover:shadow-md hover:-translate-y-0.5"
                                >
                                    {isLoadingHeatmap ? <Loader2 size={18} className="animate-spin" /> : <Brain size={18} />}
                                    Grad-CAM
                                </button>
                            )}
                        </div>

                        {error && (
                            <div className="flex gap-3 p-4 bg-rose-50 border border-rose-200 rounded-2xl text-sm font-medium text-rose-700">
                                <AlertTriangle size={18} className="flex-shrink-0 mt-0.5 text-rose-500" />
                                {error}
                            </div>
                        )}
                    </div>
                )}

                <input ref={fileInputRef} type="file" accept="image/*,.dcm,.dicom" className="hidden" onChange={e => handleFiles(e.target.files)} />

                {/* AI Reasoning */}
                {results?.reasoning && results.reasoning.length > 0 && (
                    <div className="bg-slate-50 border border-slate-200 rounded-2xl p-4">
                        <div className="flex items-center gap-2 mb-3">
                            <Brain size={16} className="text-indigo-500" />
                            <span className="text-sm font-semibold text-slate-700">AI Clinical Reasoning</span>
                        </div>
                        <div className="space-y-2">
                            {results.reasoning.map((r, i) => (
                                <div key={i} className="flex gap-2 text-sm text-slate-600">
                                    <span className="text-sky-500 font-bold mt-0.5">→</span>
                                    <span>{r}</span>
                                </div>
                            ))}
                        </div>
                    </div>
                )}
            </div>

            {/* ── Right Panel: Results ────────────────────────────────────── */}
            <div className="lg:flex-1 flex flex-col gap-4 print:w-full print:block">
                {!results && !isAnalyzing && (
                    <div className="flex-1 flex flex-col items-center justify-center text-center p-12 border-2 border-dashed border-slate-200 rounded-3xl bg-slate-50/50 min-h-72">
                        <div className="w-20 h-20 bg-gradient-to-br from-sky-100 to-indigo-100 rounded-full flex items-center justify-center mb-5">
                            <Eye size={36} className="text-sky-400" />
                        </div>
                        <h3 className="text-lg font-semibold text-slate-600 mb-2">Ready for Analysis</h3>
                        <p className="text-sm text-slate-400 max-w-xs">Upload a fundus image or DICOM and run AI analysis to see detailed findings, predictions, and recommendations.</p>
                        <div className="mt-5 flex flex-wrap gap-2 justify-center">
                            {['Diabetic Retinopathy Grading', 'Glaucoma Risk', 'Refractive Error', 'Prescription', 'Grad-CAM XAI'].map(f => (
                                <span key={f} className="text-xs bg-white border border-slate-200 text-slate-500 px-3 py-1.5 rounded-full">{f}</span>
                            ))}
                        </div>
                    </div>
                )}

                {isAnalyzing && (
                    <div className="flex-1 flex flex-col items-center justify-center gap-6 py-16">
                        <div className="relative">
                            <div className="w-24 h-24 rounded-full border-4 border-sky-100 animate-pulse" />
                            <Loader2 size={44} className="absolute inset-0 m-auto text-sky-600 animate-spin" />
                        </div>
                        <div className="text-center">
                            <h3 className="text-slate-700 font-bold text-lg mb-1">Analysing retinal scan…</h3>
                            <p className="text-sm text-slate-400 max-w-xs">Running EfficientNet-B3 DR grading · Refraction estimation · Glaucoma risk assessment</p>
                        </div>
                        <div className="flex flex-col gap-2 w-full max-w-xs">
                            {['Loading model weights', 'Preprocessing image', 'Running inference', 'Generating predictions', 'Building clinical report'].map((step, i) => (
                                <div key={step} className="flex items-center gap-2 text-xs text-slate-500">
                                    <div className="w-3.5 h-3.5 rounded-full border-2 border-sky-300 border-t-sky-600 animate-spin" style={{ animationDelay: `${i * 0.15}s` }} />
                                    {step}
                                </div>
                            ))}
                        </div>
                    </div>
                )}

                {results && (
                    <div className="flex flex-col gap-4">
                        {/* Status header */}
                        <div className="flex items-center justify-between bg-white px-5 py-3 rounded-2xl border border-slate-200">
                            <h2 className="text-xl font-bold text-slate-800">AI Findings</h2>
                            <div className="flex items-center gap-2">
                                <span className="text-xs font-bold text-emerald-600 bg-emerald-50 border border-emerald-100 px-3 py-1.5 rounded-full flex items-center gap-1.5">
                                    <CheckCircle size={13} /> Analysis Complete
                                </span>
                            </div>
                        </div>

                        {/* Tabs */}
                        <div className="flex gap-1 bg-slate-100 p-1 rounded-2xl print:hidden">
                            {([
                                ['overview', 'Overview', BarChart3],
                                ['conditions', 'Conditions', Microscope],
                                ['prescription', 'Prescription', Glasses],
                            ] as [string, string, LucideIcon][]).map(([tab, label, Icon]) => (
                                <button
                                    key={tab}
                                    onClick={() => setActiveTab(tab as any)}
                                    className={`flex-1 py-2.5 text-sm font-semibold rounded-xl flex items-center justify-center gap-1.5 transition-all ${activeTab === tab ? 'bg-white text-sky-700 shadow-sm' : 'text-slate-500 hover:text-slate-700'}`}
                                >
                                    <Icon size={14} /> {label}
                                </button>
                            ))}
                        </div>

                        {/* ─── Overview Tab ─── */}
                        {activeTab === 'overview' && (
                            <div className="space-y-4">
                                {/* Refraction Card */}
                                <div className="bg-white rounded-3xl p-6 border border-slate-100 shadow-sm hover:-translate-y-0.5 transition-all">
                                    <div className="flex items-center gap-3 mb-4">
                                        <div className="p-2 bg-sky-50 rounded-xl"><Eye size={20} className="text-sky-600" /></div>
                                        <h3 className="font-bold text-slate-800">Refractive Error Estimate</h3>
                                    </div>
                                    <div className="grid grid-cols-3 gap-3 mb-4">
                                        {[
                                            { label: 'Sphere', value: `${results.refraction.sphere >= 0 ? '+' : ''}${results.refraction.sphere.toFixed(2)}`, unit: 'D', bg: 'bg-sky-50 border-sky-200', text: 'text-sky-700' },
                                            { label: 'Cylinder', value: `${results.refraction.cylinder >= 0 ? '+' : ''}${results.refraction.cylinder.toFixed(2)}`, unit: 'D', bg: 'bg-cyan-50 border-cyan-200', text: 'text-cyan-700' },
                                            { label: 'Axis', value: `${Math.round(results.refraction.axis)}°`, unit: '', bg: 'bg-indigo-50 border-indigo-200', text: 'text-indigo-700' },
                                        ].map(({ label, value, unit, bg, text }) => (
                                            <div key={label} className={`${bg} border rounded-2xl p-3 text-center`}>
                                                <div className={`text-2xl font-bold ${text}`}>{value}</div>
                                                {unit && <div className="text-xs text-slate-400 mt-0.5">{unit}</div>}
                                                <div className="text-xs text-slate-600 mt-1">{label}</div>
                                            </div>
                                        ))}
                                    </div>
                                    {/* Type of refractive error */}
                                    {CONDITIONS.refractiveError.types.map(type => {
                                        const matches = type.trigger(results.refraction.sphere, results.refraction.cylinder)
                                        if (!matches) return null
                                        return (
                                            <div key={type.name} className="p-3 bg-sky-50/50 border border-sky-100 rounded-xl text-xs text-slate-600">
                                                <span className="font-bold text-sky-700">{type.name}: </span>{type.desc}
                                            </div>
                                        )
                                    })}
                                </div>

                                {/* Pathology Summary */}
                                <div className="bg-white rounded-3xl p-6 border border-slate-100 shadow-sm hover:-translate-y-0.5 transition-all">
                                    <div className="flex items-center gap-3 mb-4">
                                        <div className="p-2 bg-violet-50 rounded-xl"><Activity size={20} className="text-violet-600" /></div>
                                        <h3 className="font-bold text-slate-800">Pathology Screening</h3>
                                    </div>
                                    <div className="space-y-4">
                                        {[
                                            { name: 'Diabetic Retinopathy', status: results.pathology.diabetic_retinopathy.status, score: results.pathology.diabetic_retinopathy.score },
                                            { name: 'Glaucoma Risk', status: results.pathology.glaucoma.status, score: results.pathology.glaucoma.score },
                                        ].map(({ name, status, score }) => (
                                            <div key={name} className="space-y-2">
                                                <div className="flex items-center justify-between">
                                                    <span className="text-sm font-medium text-slate-700">{name}</span>
                                                    <span className={`text-xs font-semibold border px-2.5 py-0.5 rounded-full ${getSeverityBadge(status)}`}>{status}</span>
                                                </div>
                                                <ScoreBar score={score} status={status} />
                                                <div className="text-xs text-slate-400 text-right">{score.toFixed(0)} / 100</div>
                                            </div>
                                        ))}
                                    </div>
                                    <button
                                        onClick={() => setActiveTab('conditions')}
                                        className="mt-4 w-full text-center text-xs font-semibold text-indigo-600 hover:text-indigo-700 flex items-center justify-center gap-1"
                                    >
                                        <BookOpen size={13} /> View detailed condition explanations
                                    </button>
                                </div>

                                {/* Quick Spectacle */}
                                {spectacleRec && (
                                    <div className={`rounded-2xl p-4 border ${spectacleRec.recommended ? 'bg-sky-50 border-sky-200' : 'bg-green-50 border-green-200'}`}>
                                        <div className="flex items-center gap-2 mb-1">
                                            <span className="text-base">{spectacleRec.icon}</span>
                                            <span className={`text-sm font-bold ${spectacleRec.recommended ? 'text-sky-800' : 'text-green-800'}`}>
                                                Spectacle Recommendation: {spectacleRec.type}
                                            </span>
                                        </div>
                                        <p className={`text-xs leading-relaxed ${spectacleRec.recommended ? 'text-sky-700' : 'text-green-700'}`}>{spectacleRec.description}</p>
                                        {spectacleRec.recommended && (
                                            <button onClick={() => setActiveTab('prescription')} className="mt-2 text-xs font-semibold text-sky-700 underline underline-offset-2 hover:text-sky-900">
                                                View full prescription →
                                            </button>
                                        )}
                                    </div>
                                )}

                                {/* Action buttons */}
                                <div className="flex gap-2 print:hidden">
                                    <button onClick={handleExplain} disabled={isLoadingHeatmap}
                                        className="flex-1 flex items-center justify-center gap-2 border border-indigo-300 text-indigo-700 hover:bg-indigo-50 py-2.5 rounded-xl text-sm font-medium transition-colors disabled:opacity-60">
                                        {isLoadingHeatmap ? <Loader2 size={16} className="animate-spin" /> : <Zap size={16} />}
                                        {isLoadingHeatmap ? 'Generating…' : 'Grad-CAM XAI'}
                                    </button>
                                    <button onClick={() => window.print()}
                                        className="flex-1 flex items-center justify-center gap-2 bg-slate-800 text-white hover:bg-slate-700 py-2.5 rounded-xl text-sm font-medium transition-colors">
                                        <Printer size={16} /> Print Report
                                    </button>
                                </div>
                            </div>
                        )}

                        {/* ─── Conditions Tab ─── */}
                        {activeTab === 'conditions' && (
                            <div className="space-y-4">
                                {/* Diabetic Retinopathy */}
                                <ConditionExplainer
                                    title="Diabetic Retinopathy"
                                    icon={FlaskConical}
                                    color="amber"
                                    score={results.pathology.diabetic_retinopathy.score}
                                    status={results.pathology.diabetic_retinopathy.status}
                                    grade={drGrade}
                                >
                                    <InfoSection icon={BookOpen} title="What is it?">
                                        {CONDITIONS.diabeticRetinopathy.whatIsIt}
                                    </InfoSection>
                                    <InfoSection icon={HeartPulse} title="Why does it happen?">
                                        {CONDITIONS.diabeticRetinopathy.whyItHappens}
                                    </InfoSection>

                                    {/* DR Stage indicator */}
                                    <div className="mb-4">
                                        <div className="text-xs font-bold text-slate-600 uppercase tracking-wide mb-2 flex items-center gap-1"><Layers size={12} /> Staging (AI Assessed)</div>
                                        <div className="space-y-1.5">
                                            {CONDITIONS.diabeticRetinopathy.stages.map(stage => (
                                                <div key={stage.grade} className={`flex gap-3 p-3 rounded-xl border transition-all ${stage.grade === drGrade ? 'border-amber-300 bg-amber-50 shadow-sm' : 'border-slate-100 bg-white opacity-60'}`}>
                                                    <div className={`w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold flex-shrink-0 ${stage.grade === drGrade ? 'bg-amber-500 text-white' : 'bg-slate-100 text-slate-500'}`}>
                                                        {stage.grade}
                                                    </div>
                                                    <div>
                                                        <div className={`text-xs font-bold ${stage.grade === drGrade ? 'text-amber-800' : 'text-slate-600'}`}>{stage.label}</div>
                                                        <div className="text-xs text-slate-500 mt-0.5 leading-relaxed">{stage.desc}</div>
                                                    </div>
                                                    {stage.grade === drGrade && <span className="ml-auto text-xs font-bold text-amber-600 bg-amber-100 px-2 py-0.5 rounded-full self-start whitespace-nowrap">Current</span>}
                                                </div>
                                            ))}
                                        </div>
                                    </div>

                                    <InfoSection icon={ShieldAlert} title="Risk Factors">
                                        <ul className="flex flex-wrap gap-1.5 mt-1">
                                            {CONDITIONS.diabeticRetinopathy.riskFactors.map(r => (
                                                <li key={r} className="text-xs bg-amber-100 text-amber-800 px-2 py-0.5 rounded-full font-medium">{r}</li>
                                            ))}
                                        </ul>
                                    </InfoSection>
                                    <InfoSection icon={TrendingUp} title="Clinical Significance">
                                        {CONDITIONS.diabeticRetinopathy.whatItMeans}
                                    </InfoSection>
                                    <div className={`p-3 rounded-xl border text-xs font-medium leading-relaxed ${drGrade >= 3 ? 'bg-red-50 border-red-200 text-red-700' : drGrade >= 2 ? 'bg-amber-50 border-amber-200 text-amber-700' : 'bg-green-50 border-green-200 text-green-700'}`}>
                                        <strong>Recommended Action: </strong>{drInfo?.desc}
                                    </div>
                                </ConditionExplainer>

                                {/* Glaucoma */}
                                <ConditionExplainer
                                    title="Glaucoma Risk"
                                    icon={Target}
                                    color="purple"
                                    score={results.pathology.glaucoma.score}
                                    status={results.pathology.glaucoma.status}
                                >
                                    <InfoSection icon={BookOpen} title="What is it?">
                                        {CONDITIONS.glaucoma.whatIsIt}
                                    </InfoSection>
                                    <InfoSection icon={HeartPulse} title="Why does it happen?">
                                        {CONDITIONS.glaucoma.whyItHappens}
                                    </InfoSection>

                                    {/* Risk meter */}
                                    <div className="mb-4 p-3 bg-purple-50 rounded-xl border border-purple-100">
                                        <div className="text-xs font-bold text-purple-700 mb-2">Detected Risk Level</div>
                                        <div className="flex items-center gap-3">
                                            <div className="flex-1 h-3 bg-purple-100 rounded-full overflow-hidden">
                                                <div className="h-full bg-gradient-to-r from-green-400 via-amber-400 to-red-500 rounded-full" style={{ width: `${results.pathology.glaucoma.score}%` }} />
                                            </div>
                                            <span className="text-sm font-bold text-purple-800 w-14 text-right">{results.pathology.glaucoma.score.toFixed(0)}%</span>
                                        </div>
                                        <div className="flex justify-between text-xs text-slate-400 mt-1">
                                            <span>Low</span><span>Moderate</span><span>High</span>
                                        </div>
                                    </div>

                                    <InfoSection icon={ShieldAlert} title="Risk Factors">
                                        <ul className="flex flex-wrap gap-1.5 mt-1">
                                            {CONDITIONS.glaucoma.riskFactors.map(r => (
                                                <li key={r} className="text-xs bg-purple-100 text-purple-800 px-2 py-0.5 rounded-full font-medium">{r}</li>
                                            ))}
                                        </ul>
                                    </InfoSection>
                                    <InfoSection icon={TrendingUp} title="What the AI Analyses">
                                        {CONDITIONS.glaucoma.whatItMeans}
                                    </InfoSection>
                                    <div className={`p-3 rounded-xl border text-xs font-medium leading-relaxed ${glaucomaRisk >= 0.7 ? 'bg-red-50 border-red-200 text-red-700' : glaucomaRisk >= 0.4 ? 'bg-amber-50 border-amber-200 text-amber-700' : 'bg-green-50 border-green-200 text-green-700'}`}>
                                        <strong>Risk Level: </strong>
                                        {glaucomaRisk >= 0.7 ? 'High — Urgent ophthalmology referral required. Tonometry and optic disc evaluation need to be done immediately.'
                                            : glaucomaRisk >= 0.4 ? 'Moderate — Schedule comprehensive glaucoma evaluation within 3 months. Monitor IOP.'
                                            : 'Low — Routine annual monitoring is sufficient. Maintain regular eye exams.'}
                                    </div>
                                </ConditionExplainer>

                                {/* Refractive Error */}
                                <ConditionExplainer
                                    title="Refractive Error"
                                    icon={Glasses}
                                    color="sky"
                                    score={Math.min(Math.abs(sphere) * 10 + Math.abs(cylinder) * 8, 100)}
                                    status={Math.abs(sphere) < 0.5 && Math.abs(cylinder) < 0.75 ? 'Healthy' : Math.abs(sphere) <= 6 ? 'Warning' : 'Severe'}
                                >
                                    <InfoSection icon={BookOpen} title="What is it?">
                                        {CONDITIONS.refractiveError.whatIsIt}
                                    </InfoSection>
                                    <InfoSection icon={HeartPulse} title="Why does it happen?">
                                        {CONDITIONS.refractiveError.whyItHappens}
                                    </InfoSection>

                                    {/* Type */}
                                    <div className="mb-4 space-y-2">
                                        {CONDITIONS.refractiveError.types.map(type => {
                                            const match = type.trigger(sphere, cylinder)
                                            return (
                                                <div key={type.name} className={`p-3 rounded-xl border text-xs leading-relaxed transition-all ${match ? 'bg-sky-50 border-sky-200 font-medium text-sky-800' : 'bg-slate-50 border-slate-100 text-slate-400 opacity-50'}`}>
                                                    {match && <span className="text-sky-500 mr-1.5">✓</span>}
                                                    <strong>{type.name}:</strong> {type.desc}
                                                </div>
                                            )
                                        })}
                                    </div>
                                </ConditionExplainer>
                            </div>
                        )}

                        {/* ─── Prescription Tab ─── */}
                        {activeTab === 'prescription' && (
                            <div className="space-y-4">
                                {/* Spectacle recommendation */}
                                {spectacleRec && (
                                    <div className={`rounded-2xl p-5 border ${spectacleRec.recommended ? 'bg-gradient-to-br from-sky-50 to-indigo-50 border-sky-200' : 'bg-green-50 border-green-200'}`}>
                                        <div className="flex items-center gap-3 mb-3">
                                            <span className="text-3xl">{spectacleRec.icon}</span>
                                            <div>
                                                <div className={`font-bold text-base ${spectacleRec.recommended ? 'text-sky-800' : 'text-green-800'}`}>{spectacleRec.type}</div>
                                                <div className={`text-xs font-medium ${spectacleRec.urgency === 'priority' ? 'text-orange-600' : 'text-slate-500'}`}>
                                                    {spectacleRec.urgency === 'priority' ? '⚡ Priority — consult optometrist soon' : '📅 Routine follow-up recommended'}
                                                </div>
                                            </div>
                                        </div>
                                        <p className={`text-sm leading-relaxed ${spectacleRec.recommended ? 'text-sky-700' : 'text-green-700'}`}>{spectacleRec.description}</p>
                                        {spectacleRec.lensType && (
                                            <div className="mt-3 p-3 bg-white/70 rounded-xl border border-white text-xs">
                                                <span className="font-bold text-slate-700">Recommended Lens Type: </span>
                                                <span className="text-slate-600">{spectacleRec.lensType}</span>
                                            </div>
                                        )}
                                        {spectacleRec.contactLensSuitable && (
                                            <div className="mt-2 p-3 bg-white/70 rounded-xl border border-white text-xs text-slate-600">
                                                <span className="font-bold text-slate-700">Contact Lenses: </span>
                                                Suitable for this prescription. Daily disposable or monthly lenses with your optometrist's guidance.
                                            </div>
                                        )}
                                    </div>
                                )}

                                <PrescriptionCard
                                    sphere={results.refraction.sphere}
                                    cylinder={results.refraction.cylinder}
                                    axis={results.refraction.axis}
                                    drGrade={drGrade}
                                    glaucomaRisk={glaucomaRisk}
                                    date={new Date().toLocaleDateString('en-IN', { day: '2-digit', month: 'short', year: 'numeric' })}
                                />
                            </div>
                        )}
                    </div>
                )}
            </div>

            {/* Heatmap Modal */}
            {showHeatmap && heatmapData && (
                <HeatmapModal
                    heatmap={heatmapData.image}
                    explanation={heatmapData.explanation}
                    results={results}
                    onClose={() => setShowHeatmap(false)}
                />
            )}
        </div>
    )
}
