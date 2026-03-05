import React from 'react'
import { AlertCircle, CheckCircle } from 'lucide-react'

interface PathologyCardProps {
    name: string
    status: 'Healthy' | 'Warning' | 'Severe'
    severityScore: number // 0 to 100
}

export default function PathologyCard({ name, status, severityScore }: PathologyCardProps) {
    const getStatusColor = () => {
        switch (status) {
            case 'Healthy': return 'text-emerald-600 bg-emerald-50 border-emerald-100'
            case 'Warning': return 'text-amber-600 bg-amber-50 border-amber-100'
            case 'Severe': return 'text-red-600 bg-red-50 border-red-100'
        }
    }

    return (
        <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm">
            <div className="flex items-center justify-between mb-3">
                <h3 className="font-semibold text-slate-800">{name}</h3>
                <span className={`px-2.5 py-1 rounded-full text-xs font-bold border flex items-center gap-1.5 ${getStatusColor()}`}>
                    {status === 'Healthy' ? <CheckCircle size={14} /> : <AlertCircle size={14} />}
                    {status}
                </span>
            </div>

            {/* Severity Bar */}
            <div className="mt-4">
                <div className="flex justify-between text-xs text-slate-500 mb-1">
                    <span>Severity Score</span>
                    <span>{severityScore}/100</span>
                </div>
                <div className="h-2.5 w-full bg-slate-100 rounded-full overflow-hidden flex">
                    {/* Gradient Simulation using segments */}
                    <div className="h-full bg-gradient-to-r from-emerald-500 via-amber-400 to-red-500 w-full relative">
                        {/* Mask to show 'progress' */}
                        <div
                            className="absolute top-0 right-0 bottom-0 bg-slate-100/100 transition-all"
                            style={{ width: `${100 - severityScore}%` }}
                        />
                    </div>
                </div>
                <div className="flex justify-between text-[10px] text-slate-400 mt-1">
                    <span>Healthy</span>
                    <span>Critical</span>
                </div>
            </div>
        </div>
    )
}
