import React, { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { ArrowLeft, Calendar, User, AlertCircle, Heart, Image as ImageIcon, FileText, Trash2, RefreshCw } from 'lucide-react'
import ImageUploader from '../components/ImageUploader'
import { patientService, imagingService, type Patient, type ImageRecord } from '../services/api'

export default function PatientDetails() {
    const { patientId } = useParams<{ patientId: string }>()
    const navigate = useNavigate()

    const [patient, setPatient] = useState<Patient | null>(null)
    const [images, setImages] = useState<ImageRecord[]>([])
    const [isLoadingPatient, setIsLoadingPatient] = useState(true)
    const [isLoadingImages, setIsLoadingImages] = useState(true)
    const [error, setError] = useState<string | null>(null)

    // Fetch patient details
    const fetchPatient = async () => {
        if (!patientId) return

        setIsLoadingPatient(true)
        try {
            const data = await patientService.getPatient(patientId)
            setPatient(data)
        } catch (err: any) {
            console.error('Failed to fetch patient:', err)
            setError('Failed to load patient details')
        } finally {
            setIsLoadingPatient(false)
        }
    }

    // Fetch patient images
    const fetchImages = async () => {
        if (!patientId) return

        setIsLoadingImages(true)
        try {
            const data = await imagingService.getPatientImages(patientId)
            setImages(data.images)
        } catch (err: any) {
            console.error('Failed to fetch images:', err)
            // Don't set error for images, just log it
        } finally {
            setIsLoadingImages(false)
        }
    }

    useEffect(() => {
        fetchPatient()
        fetchImages()
    }, [patientId])

    // Calculate age
    const calculateAge = (dob: string): number => {
        const birthDate = new Date(dob)
        const today = new Date()
        let age = today.getFullYear() - birthDate.getFullYear()
        const monthDiff = today.getMonth() - birthDate.getMonth()

        if (monthDiff < 0 || (monthDiff === 0 && today.getDate() < birthDate.getDate())) {
            age--
        }

        return age
    }

    // Format date
    const formatDate = (dateString: string): string => {
        return new Date(dateString).toLocaleDateString('en-US', {
            year: 'numeric',
            month: 'long',
            day: 'numeric'
        })
    }

    // Handle delete image
    const handleDeleteImage = async (imageId: number) => {
        if (!window.confirm('Are you sure you want to delete this image?')) return

        try {
            await imagingService.deleteImage(imageId)
            // Refresh images
            fetchImages()
        } catch (err) {
            console.error('Failed to delete image:', err)
            alert('Failed to delete image')
        }
    }

    // Check if file is DICOM
    const isDicomFile = (image: ImageRecord): boolean => {
        return image.content_type.includes('dicom') ||
            image.file_name.toLowerCase().endsWith('.dcm') ||
            image.file_name.toLowerCase().endsWith('.dicom')
    }

    if (isLoadingPatient) {
        return (
            <div className="flex items-center justify-center h-64">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-sky-600"></div>
            </div>
        )
    }

    if (error || !patient) {
        return (
            <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg flex items-start gap-3">
                <AlertCircle size={20} className="flex-shrink-0 mt-0.5" />
                <div>
                    <p className="font-medium">Error</p>
                    <p className="text-sm mt-1">{error || 'Patient not found'}</p>
                    <button
                        onClick={() => navigate('/patients')}
                        className="mt-2 text-sm underline"
                    >
                        Back to patient list
                    </button>
                </div>
            </div>
        )
    }

    return (
        <div className="space-y-6">
            {/* Header */}
            <div className="flex items-center gap-4">
                <button
                    onClick={() => navigate('/patients')}
                    className="p-2 hover:bg-slate-100 rounded-lg transition-colors"
                >
                    <ArrowLeft size={24} />
                </button>
                <div>
                    <h2 className="text-2xl font-bold text-slate-800">{patient.full_name}</h2>
                    <p className="text-slate-500 text-sm">Patient ID: {patient.id.slice(0, 8)}...</p>
                </div>
            </div>

            {/* Patient Info Card */}
            <div className="bg-white rounded-xl border border-slate-200 p-6">
                <h3 className="font-semibold text-slate-800 mb-4">Patient Information</h3>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                    <div className="flex items-center gap-3">
                        <div className="bg-sky-100 p-3 rounded-lg">
                            <User className="text-sky-600" size={20} />
                        </div>
                        <div>
                            <p className="text-sm text-slate-500">Age</p>
                            <p className="font-semibold text-slate-800">{calculateAge(patient.dob)} years</p>
                        </div>
                    </div>

                    <div className="flex items-center gap-3">
                        <div className="bg-purple-100 p-3 rounded-lg">
                            <Calendar className="text-purple-600" size={20} />
                        </div>
                        <div>
                            <p className="text-sm text-slate-500">Date of Birth</p>
                            <p className="font-semibold text-slate-800">{formatDate(patient.dob)}</p>
                        </div>
                    </div>

                    <div className="flex items-center gap-3">
                        <div className="bg-green-100 p-3 rounded-lg">
                            <User className="text-green-600" size={20} />
                        </div>
                        <div>
                            <p className="text-sm text-slate-500">Gender</p>
                            <p className="font-semibold text-slate-800">{patient.gender}</p>
                        </div>
                    </div>

                    <div className="flex items-center gap-3">
                        <div className={`${patient.diabetes_status ? 'bg-amber-100' : 'bg-green-100'} p-3 rounded-lg`}>
                            <Heart className={`${patient.diabetes_status ? 'text-amber-600' : 'text-green-600'}`} size={20} />
                        </div>
                        <div>
                            <p className="text-sm text-slate-500">Diabetes</p>
                            <p className="font-semibold text-slate-800">{patient.diabetes_status ? 'Yes' : 'No'}</p>
                        </div>
                    </div>
                </div>
            </div>

            {/* Image Upload Section */}
            <div className="bg-white rounded-xl border border-slate-200 p-6">
                <h3 className="font-semibold text-slate-800 mb-4">Upload Medical Images</h3>
                <ImageUploader
                    patientId={patientId!}
                    onUploadSuccess={fetchImages}
                />
            </div>

            {/* Image Gallery Section */}
            <div className="bg-white rounded-xl border border-slate-200 p-6">
                <div className="flex items-center justify-between mb-4">
                    <h3 className="font-semibold text-slate-800">
                        Medical Images ({images.length})
                    </h3>
                    <button
                        onClick={fetchImages}
                        className="flex items-center gap-2 px-3 py-2 text-sm hover:bg-slate-100 rounded-lg transition-colors"
                    >
                        <RefreshCw size={16} />
                        Refresh
                    </button>
                </div>

                {isLoadingImages ? (
                    <div className="text-center py-12">
                        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-sky-600 mx-auto"></div>
                        <p className="text-slate-500 mt-2">Loading images...</p>
                    </div>
                ) : images.length === 0 ? (
                    <div className="text-center py-12 border-2 border-dashed border-slate-200 rounded-lg">
                        <ImageIcon className="mx-auto text-slate-300" size={48} />
                        <p className="text-slate-500 mt-2">No images uploaded yet</p>
                        <p className="text-sm text-slate-400">Upload images using the form above</p>
                    </div>
                ) : (
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                        {images.map((image) => (
                            <div
                                key={image.id}
                                className="border border-slate-200 rounded-lg overflow-hidden hover:shadow-lg transition-shadow group"
                            >
                                {/* Image Display */}
                                <div className="aspect-square bg-slate-100 flex items-center justify-center relative">
                                    {isDicomFile(image) ? (
                                        // DICOM Placeholder
                                        <div className="text-center p-4">
                                            <FileText className="mx-auto text-sky-600 mb-2" size={48} />
                                            <p className="font-semibold text-slate-700">DICOM File</p>
                                            <p className="text-xs text-slate-500 mt-1">{image.file_name}</p>
                                        </div>
                                    ) : (
                                        // Standard Image
                                        image.url && (
                                            <img
                                                src={image.url}
                                                alt={image.file_name}
                                                className="w-full h-full object-cover"
                                            />
                                        )
                                    )}

                                    {/* Delete Button (shows on hover) */}
                                    <button
                                        onClick={() => handleDeleteImage(image.id)}
                                        className="absolute top-2 right-2 p-2 bg-red-600 text-white rounded-full opacity-0 group-hover:opacity-100 transition-opacity hover:bg-red-700"
                                        title="Delete image"
                                    >
                                        <Trash2 size={16} />
                                    </button>
                                </div>

                                {/* Image Info */}
                                <div className="p-3 bg-white">
                                    <div className="flex items-center justify-between mb-1">
                                        <span className={`px-2 py-1 rounded text-xs font-medium ${image.image_type === 'FUNDUS'
                                                ? 'bg-green-100 text-green-700'
                                                : 'bg-blue-100 text-blue-700'
                                            }`}>
                                            {image.image_type}
                                        </span>
                                        <span className="text-xs text-slate-500">
                                            {(image.file_size / 1024 / 1024).toFixed(2)} MB
                                        </span>
                                    </div>
                                    <p className="text-sm text-slate-600 truncate" title={image.file_name}>
                                        {image.file_name}
                                    </p>
                                    <p className="text-xs text-slate-400 mt-1">
                                        {formatDate(image.uploaded_at)}
                                    </p>
                                </div>
                            </div>
                        ))}
                    </div>
                )}
            </div>
        </div>
    )
}
