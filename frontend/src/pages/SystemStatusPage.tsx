import React, { useEffect, useState } from 'react'
import { ServerCog, AlertCircle } from 'lucide-react'
import SystemHealth from '../components/SystemHealth'
import { imagingService, patientService } from '../services/api'
import { useAuthStore } from '../store/useAuthStore'

export default function SystemStatusPage() {
  const { user } = useAuthStore()
  const [patientStats, setPatientStats] = useState<any | null>(null)
  const [imagingStats, setImagingStats] = useState<any | null>(null)
  const [error, setError] = useState<string | null>(null)

  const loadStats = async () => {
    setError(null)
    try {
      const [p, i] = await Promise.all([patientService.getStatistics(), imagingService.getStatistics()])
      setPatientStats(p)
      setImagingStats(i)
    } catch {
      setError('Failed to load system statistics.')
    }
  }

  useEffect(() => {
    if (user?.role !== 'admin') return
    void loadStats()
  }, [user?.role])

  if (user?.role !== 'admin') {
    return (
      <div className="bg-white rounded-2xl premium-shadow border border-slate-200 p-8 max-w-3xl mx-auto">
        <h1 className="text-2xl font-bold text-slate-900 tracking-tight flex items-center gap-2">
          <ServerCog className="w-6 h-6 text-slate-500" />
          System Status
        </h1>
        <p className="text-slate-500 mt-2">This page is available to administrators only.</p>
      </div>
    )
  }

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      <div>
        <h1 className="text-3xl font-bold text-slate-900 tracking-tight flex items-center gap-2">
          <ServerCog className="w-7 h-7 text-sky-600" />
          System Status
        </h1>
        <p className="text-slate-500 mt-1 font-medium">Service health and operational statistics.</p>
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg flex items-start gap-3">
          <AlertCircle size={20} className="flex-shrink-0 mt-0.5" />
          <div>
            <p className="font-medium">Error</p>
            <p className="text-sm mt-1">{error}</p>
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
        <div className="xl:col-span-1">
          <SystemHealth />
        </div>
        <div className="xl:col-span-2 grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="bg-white rounded-2xl premium-shadow border border-slate-200 p-6">
            <div className="text-xs font-bold text-slate-500 uppercase tracking-wider">Patients</div>
            <div className="mt-3 space-y-2 text-sm text-slate-700">
              <div className="flex justify-between"><span>Total</span><span className="font-semibold">{patientStats?.total_patients ?? '—'}</span></div>
              <div className="flex justify-between"><span>Diabetes</span><span className="font-semibold">{patientStats?.diabetes_patients ?? '—'}</span></div>
              <div className="flex justify-between"><span>Non-diabetes</span><span className="font-semibold">{patientStats?.non_diabetes_patients ?? '—'}</span></div>
              <div className="flex justify-between"><span>Diabetes %</span><span className="font-semibold">{patientStats?.diabetes_percentage != null ? `${patientStats.diabetes_percentage.toFixed(1)}%` : '—'}</span></div>
            </div>
          </div>

          <div className="bg-white rounded-2xl premium-shadow border border-slate-200 p-6">
            <div className="text-xs font-bold text-slate-500 uppercase tracking-wider">Imaging</div>
            <div className="mt-3 space-y-2 text-sm text-slate-700">
              <div className="flex justify-between"><span>Total images</span><span className="font-semibold">{imagingStats?.total_images ?? '—'}</span></div>
              <div className="flex justify-between"><span>Total size</span><span className="font-semibold">{imagingStats?.total_size_mb != null ? `${imagingStats.total_size_mb.toFixed(2)} MB` : '—'}</span></div>
              <div className="flex justify-between"><span>Fundus</span><span className="font-semibold">{imagingStats?.by_type?.FUNDUS ?? '—'}</span></div>
              <div className="flex justify-between"><span>OCT</span><span className="font-semibold">{imagingStats?.by_type?.OCT ?? '—'}</span></div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
