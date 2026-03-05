import React from 'react'
import { Eye, FileText, CheckCircle2, Loader2 } from 'lucide-react'

const recentScans = [
    { id: 1, patient: 'John Doe', date: '2023-10-25', type: 'Fundus Information', status: 'Completed' },
    { id: 2, patient: 'Jane Smith', date: '2023-10-25', type: 'OCT Scan', status: 'Processing' },
    { id: 3, patient: 'Robert Brown', date: '2023-10-24', type: 'Fundus Information', status: 'Completed' },
    { id: 4, patient: 'Emily Davis', date: '2023-10-24', type: 'OCT Scan', status: 'Completed' },
]

export default function RecentScans() {
    return (
        <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
            <div className="p-6 border-b border-slate-100 flex items-center justify-between">
                <h3 className="font-semibold text-slate-800 flex items-center gap-2">
                    <Eye size={20} className="text-sky-600" />
                    Recent Scans
                </h3>
                <button className="text-sm text-sky-600 hover:text-sky-700 font-medium">View All</button>
            </div>

            <div className="overflow-x-auto">
                <table className="w-full text-sm text-left">
                    <thead className="text-xs text-slate-500 uppercase bg-slate-50/50">
                        <tr>
                            <th className="px-6 py-3 font-medium">Patient Name</th>
                            <th className="px-6 py-3 font-medium">Date</th>
                            <th className="px-6 py-3 font-medium">Scan Type</th>
                            <th className="px-6 py-3 font-medium">Status</th>
                        </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100">
                        {recentScans.map((scan) => (
                            <tr key={scan.id} className="hover:bg-slate-50/50 transition-colors">
                                <td className="px-6 py-4 font-medium text-slate-900">{scan.patient}</td>
                                <td className="px-6 py-4 text-slate-500">{scan.date}</td>
                                <td className="px-6 py-4 text-slate-600">{scan.type}</td>
                                <td className="px-6 py-4">
                                    <div className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold
                    ${scan.status === 'Completed' ? 'bg-emerald-50 text-emerald-700' : 'bg-blue-50 text-blue-700'}`}>
                                        {scan.status === 'Completed' ? <CheckCircle2 size={14} /> : <Loader2 size={14} className="animate-spin" />}
                                        {scan.status}
                                    </div>
                                </td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>
        </div>
    )
}
