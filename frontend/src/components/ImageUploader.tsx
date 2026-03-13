import React, { useState, useCallback } from 'react'
import { Upload, X, Image as ImageIcon, FileText, CheckCircle, AlertCircle, Loader2 } from 'lucide-react'
import { generateDicomPreview } from '../utils/dicomParser'

interface ImageUploaderProps {
    patientId: string
    onUploadSuccess?: () => void
}

interface FilePreview {
    file: File
    preview: string | null
    isGeneratingPreview?: boolean
    status: 'pending' | 'uploading' | 'success' | 'error'
    error?: string
}

export default function ImageUploader({ patientId, onUploadSuccess }: ImageUploaderProps) {
    const [files, setFiles] = useState<FilePreview[]>([])
    const [isDragging, setIsDragging] = useState(false)
    const [isUploading, setIsUploading] = useState(false)

    // Handle drag events
    const handleDragEnter = useCallback((e: React.DragEvent) => {
        e.preventDefault()
        e.stopPropagation()
        setIsDragging(true)
    }, [])

    const handleDragLeave = useCallback((e: React.DragEvent) => {
        e.preventDefault()
        e.stopPropagation()
        setIsDragging(false)
    }, [])

    const handleDragOver = useCallback((e: React.DragEvent) => {
        e.preventDefault()
        e.stopPropagation()
    }, [])

    const handleDrop = useCallback((e: React.DragEvent) => {
        e.preventDefault()
        e.stopPropagation()
        setIsDragging(false)

        const droppedFiles = Array.from(e.dataTransfer.files)
        processFiles(droppedFiles)
    }, [])

    // Handle file input change
    const handleFileInput = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
        const selectedFiles = Array.from(e.target.files || [])
        processFiles(selectedFiles)
    }, [])

    // Process and preview files
    const processFiles = (newFiles: File[]) => {
        const initialPreviews: FilePreview[] = newFiles.map(file => {
            const isImage = file.type.startsWith('image/')
            const isDicom = file.name.toLowerCase().endsWith('.dcm') || file.name.toLowerCase().endsWith('.dicom')

            return {
                file,
                preview: isImage ? URL.createObjectURL(file) : null,
                isGeneratingPreview: isDicom, // Set to true if dicom
                status: 'pending' as const
            }
        })

        // Add to state immediately
        setFiles(prev => [...prev, ...initialPreviews])

        // Asynchronously process DICOM files
        initialPreviews.forEach((filePreview) => {
            if (filePreview.isGeneratingPreview) {
                generateDicomPreview(filePreview.file)
                    .then(previewUrl => {
                        setFiles(prev => prev.map(p => 
                            p.file === filePreview.file 
                                ? { ...p, preview: previewUrl, isGeneratingPreview: false } 
                                : p
                        ))
                    })
                    .catch(err => {
                        console.error(`Failed to generate DICOM preview for ${filePreview.file.name}:`, err)
                        setFiles(prev => prev.map(p => 
                            p.file === filePreview.file 
                                ? { ...p, isGeneratingPreview: false } 
                                : p
                        ))
                    })
            }
        })
    }

    // Remove file from list
    const removeFile = (index: number) => {
        setFiles(prev => {
            const newFiles = [...prev]
            // Revoke preview URL if it exists
            if (newFiles[index].preview) {
                URL.revokeObjectURL(newFiles[index].preview!)
            }
            newFiles.splice(index, 1)
            return newFiles
        })
    }

    // Upload files
    const handleUpload = async () => {
        if (files.length === 0) return

        setIsUploading(true)

        // Import the API function dynamically
        const { uploadPatientImage } = await import('../services/api')

        // Upload each file
        for (let i = 0; i < files.length; i++) {
            if (files[i].status !== 'pending') continue

            // Update status to uploading
            setFiles(prev => {
                const updated = [...prev]
                updated[i] = { ...updated[i], status: 'uploading' }
                return updated
            })

            try {
                const formData = new FormData()
                formData.append('file', files[i].file)

                await uploadPatientImage(patientId, formData)

                // Update status to success
                setFiles(prev => {
                    const updated = [...prev]
                    updated[i] = { ...updated[i], status: 'success' }
                    return updated
                })
            } catch (error: any) {
                // Update status to error
                setFiles(prev => {
                    const updated = [...prev]
                    updated[i] = {
                        ...updated[i],
                        status: 'error',
                        error: error.response?.data?.detail || 'Upload failed'
                    }
                    return updated
                })
            }
        }

        setIsUploading(false)

        // Check if all uploads succeeded
        const allSuccess = files.every(f => f.status === 'success')
        if (allSuccess && onUploadSuccess) {
            onUploadSuccess()
            // Clear successful uploads after a delay
            setTimeout(() => {
                setFiles([])
            }, 2000)
        }
    }

    // Get file icon based on type
    const getFileIcon = (file: File) => {
        if (file.name.toLowerCase().endsWith('.dcm') || file.name.toLowerCase().endsWith('.dicom')) {
            return <FileText className="text-sky-600" size={40} />
        }
        return <ImageIcon className="text-green-600" size={40} />
    }

    return (
        <div className="space-y-4">
            {/* Drop Zone */}
            <div
                className={`border-2 border-dashed rounded-xl p-8 text-center transition-all ${isDragging
                        ? 'border-sky-500 bg-sky-50'
                        : 'border-slate-300 bg-slate-50 hover:border-sky-400'
                    }`}
                onDragEnter={handleDragEnter}
                onDragOver={handleDragOver}
                onDragLeave={handleDragLeave}
                onDrop={handleDrop}
            >
                <div className="flex flex-col items-center gap-4">
                    <div className="bg-sky-100 p-4 rounded-full">
                        <Upload className="text-sky-600" size={32} />
                    </div>

                    <div>
                        <p className="text-lg font-semibold text-slate-700 mb-1">
                            Drop medical images here
                        </p>
                        <p className="text-sm text-slate-500 mb-4">
                            Supports: JPEG, PNG, TIFF, BMP, DICOM (.dcm)
                        </p>

                        <label className="inline-flex items-center gap-2 px-6 py-3 bg-sky-600 hover:bg-sky-700 text-white rounded-lg font-medium cursor-pointer transition-colors">
                            <Upload size={18} />
                            Browse Files
                            <input
                                type="file"
                                multiple
                                accept="image/*,.dcm,.dicom"
                                onChange={handleFileInput}
                                className="hidden"
                            />
                        </label>
                    </div>
                </div>
            </div>

            {/* File Preview List */}
            {files.length > 0 && (
                <div className="space-y-3">
                    <div className="flex items-center justify-between">
                        <h3 className="font-semibold text-slate-800">
                            Selected Files ({files.length})
                        </h3>
                        <button
                            onClick={handleUpload}
                            disabled={isUploading || files.every(f => f.status !== 'pending')}
                            className="px-4 py-2 bg-sky-600 hover:bg-sky-700 disabled:bg-slate-300 text-white rounded-lg font-medium transition-colors flex items-center gap-2"
                        >
                            {isUploading ? (
                                <>
                                    <div className="animate-spin rounded-full h-4 w-4 border-2 border-white border-t-transparent" />
                                    Uploading...
                                </>
                            ) : (
                                <>
                                    <Upload size={18} />
                                    Upload All
                                </>
                            )}
                        </button>
                    </div>

                    <div className="grid gap-3">
                        {files.map((filePreview, index) => (
                            <div
                                key={index}
                                className="flex items-center gap-4 p-4 bg-white border border-slate-200 rounded-lg"
                            >
                                {/* Preview/Icon */}
                                <div className="flex-shrink-0 w-16 h-16 bg-slate-100 rounded-lg flex items-center justify-center overflow-hidden">
                                    {filePreview.isGeneratingPreview ? (
                                        <Loader2 className="animate-spin text-sky-500" size={24} />
                                    ) : filePreview.preview ? (
                                        <img
                                            src={filePreview.preview}
                                            alt={filePreview.file.name}
                                            className="w-full h-full object-cover"
                                        />
                                    ) : (
                                        getFileIcon(filePreview.file)
                                    )}
                                </div>

                                {/* File Info */}
                                <div className="flex-1 min-w-0">
                                    <p className="font-medium text-slate-800 truncate">
                                        {filePreview.file.name}
                                    </p>
                                    <p className="text-sm text-slate-500">
                                        {(filePreview.file.size / 1024 / 1024).toFixed(2)} MB
                                    </p>
                                    {filePreview.error && (
                                        <p className="text-sm text-red-600 mt-1">
                                            {filePreview.error}
                                        </p>
                                    )}
                                </div>

                                {/* Status Icon */}
                                <div className="flex-shrink-0">
                                    {filePreview.status === 'pending' && (
                                        <button
                                            onClick={() => removeFile(index)}
                                            className="p-2 hover:bg-slate-100 rounded-full transition-colors"
                                        >
                                            <X className="text-slate-400" size={20} />
                                        </button>
                                    )}
                                    {filePreview.status === 'uploading' && (
                                        <div className="animate-spin rounded-full h-6 w-6 border-2 border-sky-600 border-t-transparent" />
                                    )}
                                    {filePreview.status === 'success' && (
                                        <CheckCircle className="text-green-600" size={24} />
                                    )}
                                    {filePreview.status === 'error' && (
                                        <AlertCircle className="text-red-600" size={24} />
                                    )}
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            )}
        </div>
    )
}
