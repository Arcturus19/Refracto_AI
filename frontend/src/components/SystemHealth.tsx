import React from 'react'
import { Activity, Server, Cpu, CheckCircle2 } from 'lucide-react'

export default function SystemHealth() {
    return (
        <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-6">
            <h3 className="font-semibold text-slate-800 flex items-center gap-2 mb-6">
                <Activity size={20} className="text-sky-600" />
                System Health
            </h3>

            <div className="space-y-6">
                {/* DICOM Listener Status */}
                <div className="flex items-center justify-between p-4 bg-slate-50 rounded-lg border border-slate-100">
                    <div className="flex items-center gap-3">
                        <div className="p-2 bg-white rounded-md shadow-sm text-emerald-600">
                            <Server size={20} />
                        </div>
                        <div>
                            <div className="text-sm font-semibold text-slate-700">DICOM Listener</div>
                            <div className="text-xs text-emerald-600 flex items-center gap-1">
                                <div className="w-1.5 h-1.5 rounded-full bg-emerald-500" />
                                Active & Listening
                            </div>
                        </div>
                    </div>
                    <CheckCircle2 size={20} className="text-emerald-500" />
                </div>

                {/* GPU Utilization */}
                <div>
                    <div className="flex items-center justify-between mb-2">
                        <div className="flex items-center gap-2 text-sm font-medium text-slate-700">
                            <Cpu size={16} className="text-slate-400" />
                            GPU Utilization
                        </div>
                        <span className="text-xs font-bold text-slate-900">32%</span>
                    </div>
                    <div className="h-2 bg-slate-100 rounded-full overflow-hidden">
                        <div
                            className="h-full bg-sky-500 rounded-full transition-all duration-500"
                            style={{ width: '32%' }}
                        />
                    </div>
                    <p className="mt-2 text-xs text-slate-500">NVIDIA RTX 4090 • 45°C</p>
                </div>
            </div>
        </div>
    )
}
