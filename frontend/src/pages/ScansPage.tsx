import React, { useEffect, useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Inbox, RefreshCw, AlertCircle, FileText, Image as ImageIcon } from 'lucide-react'
import DataTable from '../components/DataTable'
import { imagingService, type ImageRecord } from '../services/api'

function formatDateTime(value: string) {
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return value
  return date.toLocaleString()
}

function formatSize(bytes: number) {
  if (!Number.isFinite(bytes) || bytes <= 0) return '—'
  const mb = bytes / 1024 / 1024
  return `${mb.toFixed(2)} MB`
}

export default function ScansPage() {
  const navigate = useNavigate()
  const [items, setItems] = useState<ImageRecord[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const fetchRecent = async () => {
    setIsLoading(true)
    setError(null)
    try {
      const data = await imagingService.getRecentImages(50)
      setItems(data)
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Failed to load recent scans.')
    } finally {
      setIsLoading(false)
    }
  }

  useEffect(() => {
    void fetchRecent()
  }, [])

  const columns = useMemo(
    () => [
      {
        header: 'Type',
        accessor: 'image_type',
        render: (row: ImageRecord) => (
          <span
            className={`px-2 py-1 rounded-full text-xs font-semibold ${
              row.image_type === 'FUNDUS' ? 'bg-emerald-50 text-emerald-700' : 'bg-sky-50 text-sky-700'
            }`}
          >
            {row.image_type}
          </span>
        ),
      },
      {
        header: 'Patient',
        accessor: 'patient_id',
        render: (row: ImageRecord) => (
          <span className="font-mono text-xs font-medium text-slate-700" title={row.patient_id}>
            {row.patient_id.slice(0, 8)}…
          </span>
        ),
      },
      {
        header: 'File',
        accessor: 'file_name',
        render: (row: ImageRecord) => (
          <div className="flex items-center gap-2">
            {row.content_type?.includes('dicom') || row.file_name.toLowerCase().endsWith('.dcm') ? (
              <FileText size={16} className="text-slate-400" />
            ) : (
              <ImageIcon size={16} className="text-slate-400" />
            )}
            <span className="text-slate-700 font-medium truncate max-w-[320px]" title={row.file_name}>
              {row.file_name}
            </span>
          </div>
        ),
      },
      {
        header: 'Uploaded',
        accessor: 'uploaded_at',
        render: (row: ImageRecord) => <span className="text-sm">{formatDateTime(row.uploaded_at)}</span>,
      },
      {
        header: 'Size',
        accessor: 'file_size',
        render: (row: ImageRecord) => <span className="text-sm text-slate-500">{formatSize(row.file_size)}</span>,
      },
    ],
    []
  )

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold text-slate-900 tracking-tight flex items-center gap-2">
            <Inbox className="w-7 h-7 text-sky-600" />
            Scans Inbox
          </h1>
          <p className="text-slate-500 mt-1 font-medium">Recent imaging uploads across all patients.</p>
        </div>

        <button
          onClick={fetchRecent}
          className="bg-white hover:bg-slate-50 text-slate-700 px-5 py-2.5 rounded-xl flex items-center gap-2 font-medium border border-slate-200 transition-all duration-200 hover:-translate-y-0.5 shadow-sm"
          title="Refresh scans"
        >
          <RefreshCw size={18} className={isLoading ? 'animate-spin' : ''} />
          Refresh
        </button>
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg flex items-start gap-3">
          <AlertCircle size={20} className="flex-shrink-0 mt-0.5" />
          <div>
            <p className="font-medium">Error Loading Scans</p>
            <p className="text-sm mt-1">{error}</p>
          </div>
        </div>
      )}

      {isLoading ? (
        <div className="bg-white rounded-2xl border border-slate-100 shadow-sm p-16 text-center animate-pulse">
          <div className="w-12 h-12 rounded-full border-4 border-slate-100 border-t-sky-500 animate-spin mx-auto mb-4" />
          <p className="text-slate-500 font-medium">Loading recent scans...</p>
        </div>
      ) : (
        <DataTable
          columns={columns}
          data={items}
          onRowClick={(row: ImageRecord) => navigate(`/scans/${row.id}`)}
        />
      )}
    </div>
  )
}
