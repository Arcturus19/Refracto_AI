import React from 'react'
import { ClipboardList } from 'lucide-react'
import { AuditTrailDashboard } from '../components/AuditTrailDashboard'
import { useAuthStore } from '../store/useAuthStore'

export default function AuditPage() {
  const { user } = useAuthStore()

  if (user?.role !== 'admin') {
    return (
      <div className="bg-white rounded-2xl premium-shadow border border-slate-200 p-8 max-w-3xl mx-auto">
        <h1 className="text-2xl font-bold text-slate-900 tracking-tight flex items-center gap-2">
          <ClipboardList className="w-6 h-6 text-slate-500" />
          Audit Trail
        </h1>
        <p className="text-slate-500 mt-2">This page is available to administrators only.</p>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-slate-900 tracking-tight flex items-center gap-2">
          <ClipboardList className="w-7 h-7 text-sky-600" />
          Audit Trail
        </h1>
        <p className="text-slate-500 mt-1 font-medium">Immutable prediction and feedback logs (no PII).</p>
      </div>

      <AuditTrailDashboard showPIIWarning />
    </div>
  )
}
