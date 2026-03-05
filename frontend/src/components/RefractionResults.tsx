import React from 'react'

export default function RefractionResults() {
    return (
        <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm">
            <h3 className="text-sm font-semibold text-slate-500 uppercase tracking-wider mb-4">Refraction Analysis</h3>

            <div className="grid grid-cols-3 gap-4">
                <div className="text-center p-3 bg-slate-50 rounded-lg border border-slate-100">
                    <span className="block text-xs text-slate-500 font-medium mb-1">Sphere (SPH)</span>
                    <span className="text-3xl font-bold text-slate-900">-2.75</span>
                </div>
                <div className="text-center p-3 bg-slate-50 rounded-lg border border-slate-100">
                    <span className="block text-xs text-slate-500 font-medium mb-1">Cylinder (CYL)</span>
                    <span className="text-3xl font-bold text-slate-900">-0.50</span>
                </div>
                <div className="text-center p-3 bg-slate-50 rounded-lg border border-slate-100">
                    <span className="block text-xs text-slate-500 font-medium mb-1">Axis</span>
                    <span className="text-3xl font-bold text-slate-900">180°</span>
                </div>
            </div>
        </div>
    )
}
