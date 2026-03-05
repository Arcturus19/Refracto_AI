import React, { useState } from 'react'
import { Save, Check, Upload, Loader2, AlertCircle } from 'lucide-react'
import ImageViewer from '../components/ImageViewer'
import RefractionResults from '../components/RefractionResults'
import PathologyCard from '../components/PathologyCard'
import AIReasoning from '../components/AIReasoning'
import { uploadScan, AnalysisResult } from '../services/api'

export default function AnalysisPage() {
    const [isAnalyzeMode, setIsAnalyzeMode] = useState(false) // Toggle to show "upload" state vs "view" state
    const [isLoading, setIsLoading] = useState(false)
    const [results, setResults] = useState<AnalysisResult | null>(null) // State to hold API results

    // Handlers
    const handleFileUpload = async () => {
        setIsLoading(true)
        setIsAnalyzeMode(true)
        try {
            // Create a dummy file for the mock
            const file = new File(["dummy"], "scan.png", { type: "image/png" })
            const data = await uploadScan(file)
            setResults(data)
        } catch (error) {
            console.error("Upload failed", error)
        } finally {
            setIsLoading(false)
        }
    }

    // Initial State: "Upload" Prompt
    // Only show the full UI if we have results or are loading. 
    // For the purpose of this task, we will default to showing the UI *after* the "upload".
    // But strictly, let's make an "Upload Action" available.

    // Render Loading State
    if (isLoading) {
        return (
            <div className="h-[calc(100vh-6rem)] flex flex-col items-center justify-center">
                <Loader2 size={48} className="text-sky-600 animate-spin mb-4" />
                <h2 className="text-xl font-bold text-slate-800">Analyzing Scan...</h2>
                <p className="text-slate-500">AI is detecting pathologies and calculating refraction.</p>
            </div>
        )
    }

    // Render Empty State (Before Upload) - Optional, but good for "connecting". 
    // For now, let's just add a button to the top to "Simulate New Upload".

    return (
        <div className="h-[calc(100vh-6rem)] flex flex-col lg:flex-row gap-6 relative">
            {/* Simulation Control (Temporary for Dev) */}
            <div className="absolute top-0 right-0 z-50 lg:hidden">
                <button onClick={handleFileUpload} className="bg-sky-600 text-white p-2 rounded-full shadow-lg">
                    <Upload size={20} />
                </button>
            </div>

            {/* Left Column: Images */}
            {/* Note: We are reusing the existing static images for the Viewer, 
          as the verification step won't actually upload a *real* new image file to the viewer component yet.
          The ImageViewer component currently hardcodes local images. 
      */}
            <div className="lg:w-3/5 h-full flex flex-col">
                <div className="flex items-center justify-between mb-4">
                    <h2 className="text-xl font-bold text-slate-800 flex items-center gap-2">
                        Image Analysis
                        <span className="text-xs font-normal text-slate-500 bg-slate-100 px-2 py-1 rounded-full">ID: #8392-L</span>
                    </h2>
                    <button
                        onClick={handleFileUpload}
                        className="text-sm bg-white border border-slate-200 text-slate-600 px-3 py-1.5 rounded-lg font-medium hover:bg-slate-50 flex items-center gap-2"
                    >
                        <Upload size={16} />
                        Simulate New Upload
                    </button>
                </div>

                <div className="flex-1 min-h-0">
                    <ImageViewer />
                </div>
            </div>

            {/* Right Column: AI Results */}
            <div className="lg:w-2/5 h-full flex flex-col">
                {results ? (
                    <>
                        <div className="flex items-center justify-between mb-4 animate-fade-in">
                            <h2 className="text-xl font-bold text-slate-800">AI Findings</h2>
                            <span className="text-xs font-semibold text-emerald-600 bg-emerald-50 border border-emerald-100 px-3 py-1 rounded-full">
                                High Confidence (99.2%)
                            </span>
                        </div>

                        <div className="flex-1 overflow-y-auto pr-2 space-y-6 pb-20 animate-fade-in">

                            {/* Section A: Refraction */}
                            <RefractionResults />
                            {/* Note: RefractionResults component is currently static. 
                        To make it dynamic, we would pass props like: 
                        <RefractionResults data={results.refraction} />
                        For this task step, I will leave it static but handled by the loading state flow.
                    */}

                            {/* Section B: Pathology */}
                            <div className="space-y-4">
                                <h3 className="text-sm font-semibold text-slate-500 uppercase tracking-wider">Pathology Detection</h3>
                                <PathologyCard
                                    name="Diabetic Retinopathy"
                                    status={results.pathology.diabetic_retinopathy.status}
                                    severityScore={results.pathology.diabetic_retinopathy.score}
                                />
                                <PathologyCard
                                    name="Glaucoma"
                                    status={results.pathology.glaucoma.status}
                                    severityScore={results.pathology.glaucoma.score}
                                />
                            </div>

                            {/* Section C: Explanation */}
                            {/* AIReasoning is also static currently. */}
                            <AIReasoning />
                        </div>

                        {/* Bottom Actions */}
                        <div className="pt-4 mt-auto border-t border-slate-200 animate-fade-in">
                            <button className="w-full bg-sky-600 hover:bg-sky-700 text-white font-semibold py-3.5 px-6 rounded-xl flex items-center justify-center gap-2 shadow-lg shadow-sky-200 transition-all transform hover:scale-[1.02] active:scale-[0.98]">
                                <Check size={20} />
                                Verify & Save Diagnosis
                            </button>
                        </div>
                    </>
                ) : (
                    // Empty State / Prompt to Upload
                    <div className="flex-1 flex flex-col items-center justify-center text-center p-6 border-2 border-dashed border-slate-200 rounded-xl bg-slate-50/50">
                        <div className="w-16 h-16 bg-white rounded-full flex items-center justify-center shadow-sm mb-4">
                            <Upload size={32} className="text-slate-400" />
                        </div>
                        <h3 className="text-lg font-semibold text-slate-700 mb-2">No Analysis Yet</h3>
                        <p className="text-slate-500 mb-6 max-w-xs">Upload a scan or click "Simulate New Upload" to start the AI analysis.</p>
                        <button
                            onClick={handleFileUpload}
                            className="bg-sky-600 hover:bg-sky-700 text-white px-6 py-2.5 rounded-lg font-medium transition-colors shadow-md shadow-sky-100"
                        >
                            Start Analysis
                        </button>
                    </div>
                )}
            </div>
        </div>
    )
}

