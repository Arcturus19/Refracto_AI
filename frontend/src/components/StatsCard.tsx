import React from 'react'
import { LucideIcon } from 'lucide-react'

interface StatsCardProps {
    label: string
    value: string | number
    icon: LucideIcon
    trend?: string
    trendUp?: boolean
    description?: string
    alert?: boolean
}

export default function StatsCard({ label, value, icon: Icon, trend, trendUp, description, alert }: StatsCardProps) {
    return (
        <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm hover:shadow-md transition-shadow">
            <div className="flex items-start justify-between">
                <div>
                    <p className="text-sm font-medium text-slate-500">{label}</p>
                    <h3 className={`text-2xl font-bold mt-2 ${alert ? 'text-red-600' : 'text-slate-900'}`}>{value}</h3>

                    {(trend || description) && (
                        <div className="mt-2 flex items-center text-xs">
                            {trend && (
                                <span className={`font-medium ${trendUp ? 'text-emerald-600' : 'text-slate-600'}`}>
                                    {trend}
                                </span>
                            )}
                            {description && <span className="text-slate-400 ml-1">{description}</span>}
                        </div>
                    )}
                </div>
                <div className={`p-3 rounded-lg ${alert ? 'bg-red-50 text-red-600' : 'bg-sky-50 text-sky-600'}`}>
                    <Icon size={24} />
                </div>
            </div>
        </div>
    )
}
