import React, { useState, useCallback, useRef } from 'react'
import {
    Upload, Loader2, Brain, Eye, Activity, AlertTriangle,
    CheckCircle, FileText, Zap, ChevronDown, ChevronUp,
    X, Image as ImageIcon, Sparkles
} from 'lucide-react'
import { useSearchParams } from 'react-router-dom'
import { mlService, analyzeScan, AnalysisResult } from '../services/api'
import PrescriptionCard from '../components/PrescriptionCard'

// ─── Heatmap Modal ────────────────────────────────────────────────────────────
function HeatmapModal({ heatmap, explanation, onClose }: { heatmap: string; explanation: string; onClose: () => void }) {
    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm" onClick={onClose}>
            <div className="bg-white rounded-2xl shadow-2xl max-w-lg w-full overflow-hidden" onClick={e => e.stopPropagation()}>
                <div className="bg-gradient-to-r from-indigo-600 to-purple-600 px-5 py-4 flex items-center justify-between">
                    <div className="flex items-center gap-2 text-white">
                        <Brain size={20} />
                        <span className="font-bold">Grad-CAM Explanation</span>
                    </div>
                    <button onClick={onClose} className="text-white/70 hover:text-white">
                        <X size={20} />
                    </button>
                </div>
                <div className="p-5">
                    <img src={heatmap} alt="Grad-CAM heatmap" className="w-full rounded-xl border border-slate-200 mb-4" />
                    <div className="flex gap-3 text-xs text-slate-600 mb-4">
                        <div className="flex items-center gap-1.5">
                            <div className="w-3 h-3 rounded-full bg-red-500" /> High influence
                        </div>
                        <div className="flex items-center gap-1.5">
                            <div className="w-3 h-3 rounded-full bg-yellow-400" /> Medium influence
                        </div>
                        <div className="flex items-center gap-1.5">
                            <div className="w-3 h-3 rounded-full bg-blue-500" /> Low influence
                        </div>
                    </div>
                    <p className="text-sm text-slate-700 bg-indigo-50 border border-indigo-100 rounded-xl p-3">{explanation}</p>
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

    // XAI / Heatmap state
    const [heatmapData, setHeatmapData] = useState<{ image: string; explanation: string } | null>(null)
    const [isLoadingHeatmap, setIsLoadingHeatmap] = useState(false)
    const [showHeatmap, setShowHeatmap] = useState(false)

    // Prescription toggle
    const [showPrescription, setShowPrescription] = useState(false)

    const fileInputRef = useRef<HTMLInputElement>(null)

    // ── File handling ────────────────────────────────────────────────────────────
    const handleFiles = useCallback((files: FileList | null) => {
        if (!files || files.length === 0) return
        const file = files[0]
        const allowed = ['image/jpeg', 'image/png', 'image/tiff', 'image/bmp', 'image/webp', '']
        const isDicom = file.name.toLowerCase().endsWith('.dcm') || file.name.toLowerCase().endsWith('.dicom')
        if (!isDicom && !file.type.startsWith('image/')) {
            setError('Please upload an image file (JPEG, PNG, TIFF, BMP) or a DICOM (.dcm) file.')
            return
        }
        setSelectedFile(file)
        setResults(null)
        setError(null)
        setHeatmapData(null)
        setShowPrescription(false)
        if (!isDicom) {
            const url = URL.createObjectURL(file)
            setPreviewUrl(url)
        } else {
            setPreviewUrl(null)
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
        setShowPrescription(false)
        try {
            const data = await analyzeScan(selectedFile, patientId)
            setResults(data)
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
            setHeatmapData({
                image: xaiResult.heatmap_base64,
                explanation: xaiResult.explanation,
            })
            setShowHeatmap(true)
        } catch {
            setError('Grad-CAM explanation failed. Model may not be loaded yet.')
        } finally {
            setIsLoadingHeatmap(false)
        }
    }

    const isDicomFile = selectedFile?.name.toLowerCase().endsWith('.dcm') || selectedFile?.name.toLowerCase().endsWith('.dicom')

    return (
        <div className="min-h-[calc(100vh-6rem)] flex flex-col lg:flex-row gap-6">

            {/* ── Left Panel: Upload ─────────────────────────────────────── */}
            <div className="lg:w-1/2 flex flex-col gap-4">
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
                        className={`flex-1 min-h-72 border-2 border-dashed rounded-2xl flex flex-col items-center justify-center gap-4 p-8 text-center
              transition-all cursor-pointer select-none
              ${isDragging ? 'border-sky-500 bg-sky-50 scale-[1.01]' : 'border-slate-300 bg-slate-50 hover:border-sky-400 hover:bg-sky-50/50'}`}
                        onDragOver={e => { e.preventDefault(); setIsDragging(true) }}
                        onDragLeave={() => setIsDragging(false)}
                        onDrop={handleDrop}
                        onClick={() => fileInputRef.current?.click()}
                    >
                        <div className={`p-5 rounded-2xl ${isDragging ? 'bg-sky-200' : 'bg-sky-100'} transition-colors`}>
                            <Upload className="text-sky-600" size={36} />
                        </div>
                        <div>
                            <p className="text-lg font-semibold text-slate-700 mb-1">Drop your medical scan here</p>
                            <p className="text-sm text-slate-500">Fundus, OCT, or DICOM (.dcm) — or click to browse</p>
                        </div>
                        <div className="flex flex-wrap justify-center gap-2">
                            {['JPEG', 'PNG', 'TIFF', 'DICOM'].map(t => (
                                <span key={t} className="text-xs bg-white border border-slate-200 text-slate-500 px-2.5 py-1 rounded-full">{t}</span>
                            ))}
                        </div>
                    </div>
                ) : (
                    <div className="flex flex-col gap-4">
                        {/* Image preview */}
                        <div className="relative bg-slate-900 rounded-2xl overflow-hidden aspect-square w-full flex items-center justify-center">
                            {previewUrl ? (
                                <img src={previewUrl} alt="Selected scan" className="w-full h-full object-contain" />
                            ) : (
                                <div className="flex flex-col items-center gap-3 text-slate-400">
                                    <FileText size={48} />
                                    <span className="text-sm">DICOM file — {(selectedFile.size / 1024 / 1024).toFixed(2)} MB</span>
                                </div>
                            )}
                            <button
                                onClick={clearFile}
                                className="absolute top-3 right-3 bg-white/90 text-slate-600 hover:bg-white rounded-full p-1.5 shadow-md"
                            >
                                <X size={16} />
                            </button>
                            <div className="absolute bottom-3 left-3 bg-black/50 backdrop-blur-sm text-white text-xs px-3 py-1.5 rounded-full">
                                {isDicomFile ? '🩻 DICOM' : '🖼️ Image'} · {selectedFile.name.length > 28 ? selectedFile.name.slice(0, 25) + '…' : selectedFile.name}
                            </div>
                        </div>

                        {/* Action buttons */}
                        <div className="flex gap-3">
                            <button
                                onClick={handleAnalyze}
                                disabled={isAnalyzing}
                                className="flex-1 bg-sky-600 hover:bg-sky-700 disabled:opacity-60 text-white font-semibold py-3 rounded-xl flex items-center justify-center gap-2 shadow-lg shadow-sky-200 transition-all"
                            >
                                {isAnalyzing ? <Loader2 size={20} className="animate-spin" /> : <Sparkles size={20} />}
                                {isAnalyzing ? 'Analyzing…' : 'Run AI Analysis'}
                            </button>

                            {results && (
                                <button
                                    onClick={handleExplain}
                                    disabled={isLoadingHeatmap}
                                    className="flex items-center gap-2 px-4 py-3 border border-indigo-300 text-indigo-700 hover:bg-indigo-50 disabled:opacity-60 rounded-xl font-medium text-sm transition-colors"
                                >
                                    {isLoadingHeatmap ? <Loader2 size={16} className="animate-spin" /> : <Brain size={16} />}
                                    Grad-CAM
                                </button>
                            )}
                        </div>

                        {error && (
                            <div className="flex gap-2 p-3 bg-red-50 border border-red-200 rounded-xl text-sm text-red-700">
                                <AlertTriangle size={16} className="flex-shrink-0 mt-0.5 text-red-500" />
                                {error}
                            </div>
                        )}
                    </div>
                )}

                <input
                    ref={fileInputRef}
                    type="file"
                    accept="image/*,.dcm,.dicom"
                    className="hidden"
                    onChange={e => handleFiles(e.target.files)}
                />

                {/* Reasoning panel */}
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
            <div className="lg:w-1/2 flex flex-col gap-4">
                {!results && !isAnalyzing && (
                    <div className="flex-1 flex flex-col items-center justify-center text-center p-8 border-2 border-dashed border-slate-200 rounded-2xl bg-slate-50/50 min-h-72">
                        <div className="w-16 h-16 bg-gradient-to-br from-sky-100 to-indigo-100 rounded-full flex items-center justify-center mb-4">
                            <Eye size={32} className="text-sky-400" />
                        </div>
                        <h3 className="text-lg font-semibold text-slate-600 mb-2">No Analysis Yet</h3>
                        <p className="text-sm text-slate-400 max-w-xs">Upload a fundus image or DICOM file and click "Run AI Analysis" to see results.</p>
                    </div>
                )}

                {isAnalyzing && (
                    <div className="flex-1 flex flex-col items-center justify-center gap-4 py-16">
                        <div className="relative">
                            <div className="w-20 h-20 rounded-full border-4 border-sky-100 animate-pulse" />
                            <Loader2 size={40} className="absolute inset-0 m-auto text-sky-600 animate-spin" />
                        </div>
                        <h3 className="text-slate-700 font-semibold">Analyzing scan…</h3>
                        <p className="text-sm text-slate-400 text-center max-w-xs">
                            Running EfficientNet-B3 DR grading, refraction estimation, and glaucoma risk assessment.
                        </p>
                    </div>
                )}

                {results && (
                    <div className="flex flex-col gap-4">
                        {/* Header */}
                        <div className="flex items-center justify-between">
                            <h2 className="text-xl font-bold text-slate-800">AI Findings</h2>
                            <span className="text-xs font-semibold text-emerald-600 bg-emerald-50 border border-emerald-200 px-3 py-1 rounded-full flex items-center gap-1">
                                <CheckCircle size={12} />
                                Analysis Complete
                            </span>
                        </div>

                        {/* Refraction Card */}
                        <div className="bg-white border border-slate-200 rounded-2xl p-4 shadow-sm">
                            <div className="flex items-center gap-2 mb-4">
                                <Eye size={18} className="text-sky-600" />
                                <h3 className="font-semibold text-slate-700">Refractive Error Estimate</h3>
                            </div>
                            <div className="grid grid-cols-3 gap-3">
                                {[
                                    { label: 'Sphere', value: `${results.refraction.sphere >= 0 ? '+' : ''}${results.refraction.sphere.toFixed(2)}`, unit: 'D', bg: 'bg-sky-50 border-sky-200', text: 'text-sky-700' },
                                    { label: 'Cylinder', value: `${results.refraction.cylinder >= 0 ? '+' : ''}${results.refraction.cylinder.toFixed(2)}`, unit: 'D', bg: 'bg-cyan-50 border-cyan-200', text: 'text-cyan-700' },
                                    { label: 'Axis', value: `${Math.round(results.refraction.axis)}°`, unit: '', bg: 'bg-indigo-50 border-indigo-200', text: 'text-indigo-700' },
                                ].map(({ label, value, unit, bg, text }) => (
                                    <div key={label} className={`${bg} border rounded-xl p-3 text-center`}>
                                        <div className={`text-2xl font-bold ${text}`}>{value}</div>
                                        {unit && <div className="text-xs text-slate-400 mt-0.5">{unit}</div>}
                                        <div className="text-xs text-slate-600 mt-1">{label}</div>
                                    </div>
                                ))}
                            </div>
                        </div>

                        {/* Pathology Cards */}
                        <div className="bg-white border border-slate-200 rounded-2xl p-4 shadow-sm">
                            <div className="flex items-center gap-2 mb-4">
                                <Activity size={18} className="text-violet-600" />
                                <h3 className="font-semibold text-slate-700">Pathology Detection</h3>
                            </div>
                            <div className="space-y-3">
                                {[
                                    {
                                        name: 'Diabetic Retinopathy',
                                        status: results.pathology.diabetic_retinopathy.status,
                                        score: results.pathology.diabetic_retinopathy.score,
                                    },
                                    {
                                        name: 'Glaucoma Risk',
                                        status: results.pathology.glaucoma.status,
                                        score: results.pathology.glaucoma.score,
                                    },
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
                        </div>

                        {/* Prescription toggle */}
                        <button
                            onClick={() => setShowPrescription(p => !p)}
                            className="flex items-center justify-between w-full bg-gradient-to-r from-sky-600 to-cyan-500 text-white px-4 py-3 rounded-xl font-semibold text-sm shadow-lg shadow-sky-200 hover:from-sky-700 transition-all"
                        >
                            <div className="flex items-center gap-2">
                                <FileText size={18} />
                                View Clinical Prescription
                            </div>
                            {showPrescription ? <ChevronUp size={18} /> : <ChevronDown size={18} />}
                        </button>

                        {showPrescription && (
                            <PrescriptionCard
                                sphere={results.refraction.sphere}
                                cylinder={results.refraction.cylinder}
                                axis={results.refraction.axis}
                                drGrade={Math.round(results.pathology.diabetic_retinopathy.score / 25)}
                                glaucomaRisk={results.pathology.glaucoma.score / 100}
                                date={new Date().toLocaleDateString('en-IN', { day: '2-digit', month: 'short', year: 'numeric' })}
                            />
                        )}

                        {/* Grad-CAM button (inline alternative) */}
                        {!results && null}
                        <div className="flex gap-2">
                            <button
                                onClick={handleExplain}
                                disabled={isLoadingHeatmap}
                                className="flex-1 flex items-center justify-center gap-2 border border-indigo-300 text-indigo-700 hover:bg-indigo-50 py-2.5 rounded-xl text-sm font-medium transition-colors disabled:opacity-60"
                            >
                                {isLoadingHeatmap ? <Loader2 size={16} className="animate-spin" /> : <Zap size={16} />}
                                {isLoadingHeatmap ? 'Generating heatmap…' : 'View Grad-CAM XAI'}
                            </button>
                        </div>
                    </div>
                )}
            </div>

            {/* Heatmap Modal */}
            {showHeatmap && heatmapData && (
                <HeatmapModal
                    heatmap={heatmapData.image}
                    explanation={heatmapData.explanation}
                    onClose={() => setShowHeatmap(false)}
                />
            )}
        </div>
    )
}
