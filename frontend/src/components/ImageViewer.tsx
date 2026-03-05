import React, { useState } from 'react'
import { Eye, Layers, Flame } from 'lucide-react'

export default function ImageViewer() {
    const [activeTab, setActiveTab] = useState<'fundus' | 'oct'>('fundus')
    const [showHeatmap, setShowHeatmap] = useState(false)

    return (
        <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden flex flex-col h-full">
            {/* Tabs */}
            <div className="flex border-b border-slate-200">
                <button
                    onClick={() => setActiveTab('fundus')}
                    className={`
            flex-1 flex items-center justify-center gap-2 py-4 text-sm font-semibold transition-colors
            ${activeTab === 'fundus'
                            ? 'bg-sky-50 text-sky-700 border-b-2 border-sky-600'
                            : 'text-slate-500 hover:bg-slate-50 hover:text-slate-700'}
          `}
                >
                    <Eye size={18} />
                    Fundus Image
                </button>
                <button
                    onClick={() => setActiveTab('oct')}
                    className={`
            flex-1 flex items-center justify-center gap-2 py-4 text-sm font-semibold transition-colors
            ${activeTab === 'oct'
                            ? 'bg-sky-50 text-sky-700 border-b-2 border-sky-600'
                            : 'text-slate-500 hover:bg-slate-50 hover:text-slate-700'}
          `}
                >
                    <Layers size={18} />
                    OCT Scan
                </button>
            </div>

            {/* Image Area */}
            <div className="flex-1 bg-slate-900 relative flex items-center justify-center p-4 min-h-[400px]">
                {activeTab === 'fundus' ? (
                    <div className="relative max-w-full max-h-full">
                        <img
                            src="/fundus_scan.png"
                            alt="Fundus Scan"
                            className="max-w-full max-h-[500px] object-contain rounded-lg shadow-lg"
                        />
                        {showHeatmap && (
                            <img
                                src="/heatmap_overlay.png"
                                alt="Heatmap Overlay"
                                className="absolute inset-0 w-full h-full object-contain opacity-50 pointer-events-none mix-blend-overlay rounded-lg"
                            />
                        )}
                    </div>
                ) : (
                    <div className="relative max-w-full max-h-full">
                        <img
                            src="/oct_scan.png"
                            alt="OCT Scan"
                            className="max-w-full max-h-[500px] object-contain rounded-lg shadow-lg"
                        />
                        {/* Heatmap logic for OCT could be added here if we had a specific OCT heatmap */}
                    </div>
                )}

                {/* Heatmap Toggle (Overlay on Image Area) */}
                {activeTab === 'fundus' && (
                    <div className="absolute bottom-6 right-6 z-10">
                        <button
                            onClick={() => setShowHeatmap(!showHeatmap)}
                            className={`
                flex items-center gap-2 px-4 py-2 rounded-full font-medium shadow-lg transition-all
                ${showHeatmap
                                    ? 'bg-sky-600 text-white hover:bg-sky-700'
                                    : 'bg-white text-slate-700 hover:bg-slate-50'}
              `}
                        >
                            <Flame size={18} className={showHeatmap ? 'fill-current' : ''} />
                            {showHeatmap ? 'Hide XAI Heatmap' : 'Show XAI Heatmap'}
                        </button>
                    </div>
                )}
            </div>
        </div>
    )
}
