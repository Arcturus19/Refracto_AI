import React, { useEffect, useMemo, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { ArrowLeft, FileText, Image as ImageIcon, ExternalLink, RefreshCw, Trash2, AlertCircle } from 'lucide-react'
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

export default function ScanDetailsPage() {
  const { imageId } = useParams<{ imageId: string }>()
  const navigate = useNavigate()
  const numericId = useMemo(() => Number(imageId), [imageId])

  const [image, setImage] = useState<ImageRecord | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const isDicom = useMemo(() => {
    if (!image) return false
    return (
      image.content_type?.includes('dicom') ||
      image.file_name.toLowerCase().endsWith('.dcm') ||
      image.file_name.toLowerCase().endsWith('.dicom')
    )
  }, [image])

  const fetchImage = async () => {
    if (!Number.isFinite(numericId)) {
      setError('Invalid scan id')
      setIsLoading(false)
      return
    }

    setIsLoading(true)
    setError(null)
    try {
      const data = await imagingService.getImageById(numericId)
      setImage(data)
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Failed to load scan details.')
    } finally {
      setIsLoading(false)
    }
  }

  useEffect(() => {
    void fetchImage()
  }, [numericId])

  const handleDelete = async () => {
    if (!image) return
    if (!window.confirm('Delete this scan? This cannot be undone.')) return

    try {
      await imagingService.deleteImage(image.id)
      navigate('/scans')
    } catch {
      setError('Failed to delete scan.')
    }
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-sky-600" />
      </div>
    )
  }

  if (error || !image) {
    return (
      <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg flex items-start gap-3">
        <AlertCircle size={20} className="flex-shrink-0 mt-0.5" />
        <div>
          <p className="font-medium">Error</p>
          <p className="text-sm mt-1">{error || 'Scan not found'}</p>
          <button onClick={() => navigate('/scans')} className="mt-2 text-sm underline">
            Back to scans inbox
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6 max-w-6xl mx-auto">
      <div className="flex items-center justify-between gap-4">
        <div className="flex items-center gap-4">
          <button onClick={() => navigate('/scans')} className="p-2 hover:bg-slate-100 rounded-lg transition-colors">
            <ArrowLeft size={24} />
          </button>
          <div>
            <h1 className="text-2xl font-bold text-slate-900 tracking-tight">Scan #{image.id}</h1>
            <p className="text-slate-500 text-sm">{image.file_name}</p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={fetchImage}
            className="inline-flex items-center gap-2 px-4 py-2.5 rounded-xl bg-white border border-slate-200 text-slate-700 font-semibold hover:bg-slate-50"
          >
            <RefreshCw className={`w-4 h-4 ${isLoading ? 'animate-spin' : ''}`} />
            Refresh
          </button>
          <button
            onClick={handleDelete}
            className="inline-flex items-center gap-2 px-4 py-2.5 rounded-xl bg-rose-600 text-white font-semibold hover:bg-rose-700"
            title="Delete scan"
          >
            <Trash2 className="w-4 h-4" />
            Delete
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <section className="bg-white rounded-2xl premium-shadow border border-slate-200 overflow-hidden">
          <div className="px-6 py-4 border-b border-slate-100 flex items-center justify-between">
            <div className="font-bold text-slate-800 flex items-center gap-2">
              {isDicom ? <FileText size={18} className="text-slate-400" /> : <ImageIcon size={18} className="text-slate-400" />}
              Preview
            </div>
            {image.url && !isDicom && (
              <a
                href={image.url}
                target="_blank"
                rel="noreferrer"
                className="text-sm font-semibold text-sky-700 hover:text-sky-800 inline-flex items-center gap-1"
              >
                Open <ExternalLink size={14} />
              </a>
            )}
          </div>

          <div className="bg-slate-900 aspect-square flex items-center justify-center p-4">
            {isDicom ? (
              <div className="text-center text-slate-300">
                <FileText className="mx-auto mb-2" size={52} />
                <p className="font-semibold">DICOM file</p>
                <p className="text-xs text-slate-400 mt-1">Preview is not generated here.</p>
              </div>
            ) : image.url ? (
              <img src={image.url} alt={image.file_name} className="max-w-full max-h-full object-contain rounded-lg shadow-lg" />
            ) : (
              <div className="text-center text-slate-300">
                <ImageIcon className="mx-auto mb-2" size={52} />
                <p className="font-semibold">No preview URL available</p>
              </div>
            )}
          </div>
        </section>

        <section className="bg-white rounded-2xl premium-shadow border border-slate-200 p-6 space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-bold text-slate-800">Metadata</h2>
            <button
              onClick={() => navigate(`/analysis?patientId=${encodeURIComponent(image.patient_id)}`)}
              className="inline-flex items-center gap-2 px-4 py-2.5 rounded-xl bg-sky-600 text-white font-semibold hover:bg-sky-700"
              title="Open analysis page for this patient"
            >
              Analyze
            </button>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div className="p-4 bg-slate-50 rounded-2xl border border-slate-100">
              <div className="text-xs font-bold text-slate-500 uppercase tracking-wider">Patient</div>
              <div className="mt-1 font-mono text-sm text-slate-800">{image.patient_id}</div>
              <button
                onClick={() => navigate(`/patients/${image.patient_id}`)}
                className="mt-2 text-sm font-semibold text-sky-700 hover:text-sky-800"
              >
                View patient
              </button>
            </div>
            <div className="p-4 bg-slate-50 rounded-2xl border border-slate-100">
              <div className="text-xs font-bold text-slate-500 uppercase tracking-wider">Type</div>
              <div className="mt-1 text-sm font-semibold text-slate-800">{image.image_type}</div>
              <div className="text-xs text-slate-500 mt-1">{image.content_type}</div>
            </div>
            <div className="p-4 bg-slate-50 rounded-2xl border border-slate-100">
              <div className="text-xs font-bold text-slate-500 uppercase tracking-wider">Uploaded</div>
              <div className="mt-1 text-sm font-semibold text-slate-800">{formatDateTime(image.uploaded_at)}</div>
            </div>
            <div className="p-4 bg-slate-50 rounded-2xl border border-slate-100">
              <div className="text-xs font-bold text-slate-500 uppercase tracking-wider">Size</div>
              <div className="mt-1 text-sm font-semibold text-slate-800">{formatSize(image.file_size)}</div>
            </div>
          </div>

          <div className="text-xs text-slate-500">
            Note: Analysis requires selecting the file again (current backend API does not expose “analyze by image id”).
          </div>
        </section>
      </div>
    </div>
  )
}
