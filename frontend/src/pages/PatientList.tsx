import React, { useState, useEffect } from 'react'
import { Plus, Search, Eye, Filter, RefreshCw, AlertCircle } from 'lucide-react'
import DataTable from '../components/DataTable'
import AddPatientModal from '../components/AddPatientModal'
import { patientService, type Patient } from '../services/api'

export default function PatientList() {
    const [patients, setPatients] = useState<Patient[]>([])
    const [searchQuery, setSearchQuery] = useState('')
    const [isModalOpen, setIsModalOpen] = useState(false)
    const [isLoading, setIsLoading] = useState(true)
    const [error, setError] = useState<string | null>(null)

    // Fetch patients from backend
    const fetchPatients = async (search?: string) => {
        setIsLoading(true)
        setError(null)

        try {
            const data = await patientService.getPatients(search)
            setPatients(data)
        } catch (err: any) {
            console.error('Failed to fetch patients:', err)
            setError(err.response?.data?.detail || 'Failed to load patients. Please try again.')
        } finally {
            setIsLoading(false)
        }
    }

    // Initial fetch on component mount
    useEffect(() => {
        fetchPatients()
    }, [])

    // Debounced search - fetch from backend when search query changes
    useEffect(() => {
        const timeoutId = setTimeout(() => {
            if (searchQuery.trim()) {
                fetchPatients(searchQuery.trim())
            } else {
                fetchPatients()
            }
        }, 500) // 500ms debounce

        return () => clearTimeout(timeoutId)
    }, [searchQuery])

    // Calculate age from date of birth
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

    // Format date for display
    const formatDate = (dateString: string): string => {
        return new Date(dateString).toLocaleDateString('en-US', {
            year: 'numeric',
            month: 'short',
            day: 'numeric'
        })
    }

    const handleAddPatient = async (newData: any) => {
        try {
            // Create patient via API
            const newPatient = await patientService.createPatient({
                full_name: newData.name,
                dob: newData.dob,
                gender: newData.gender || 'Other',
                diabetes_status: false
            })

            // Refresh patient list
            await fetchPatients()

            console.log('✓ Patient created:', newPatient.full_name)
        } catch (err: any) {
            console.error('Failed to create patient:', err)
            setError(err.response?.data?.detail || 'Failed to create patient.')
        }
    }

    const columns = [
        {
            header: 'Patient ID',
            accessor: 'id',
            render: (row: Patient) => (
                <span className="font-mono text-xs font-medium text-slate-700 truncate block max-w-[120px]" title={row.id}>
                    {row.id.slice(0, 8)}...
                </span>
            )
        },
        {
            header: 'Name',
            accessor: 'full_name',
            render: (row: Patient) => <span className="font-semibold text-slate-900">{row.full_name}</span>
        },
        {
            header: 'Age',
            accessor: 'age',
            render: (row: Patient) => <span>{calculateAge(row.dob)}</span>
        },
        {
            header: 'Gender',
            accessor: 'gender'
        },
        {
            header: 'Last Visit',
            accessor: 'created_at',
            render: (row: Patient) => <span className="text-sm">{formatDate(row.created_at)}</span>
        },
        {
            header: 'Diabetes',
            accessor: 'diabetes_status',
            render: (row: Patient) => (
                <span className={`px-2 py-1 rounded-full text-xs font-medium ${row.diabetes_status
                        ? 'bg-amber-100 text-amber-700'
                        : 'bg-green-100 text-green-700'
                    }`}>
                    {row.diabetes_status ? 'Yes' : 'No'}
                </span>
            )
        },
        {
            header: 'Actions',
            accessor: 'actions',
            render: (row: Patient) => (
                <button
                    className="text-sky-600 hover:text-sky-700 hover:bg-sky-50 p-2 rounded-full transition-colors"
                    title="View Details"
                    onClick={(e) => {
                        e.stopPropagation()
                        console.log('View patient:', row.id)
                    }}
                >
                    <Eye size={18} />
                </button>
            )
        }
    ]

    return (
        <div className="space-y-6">
            {/* Header & Controls */}
            <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
                <div>
                    <h2 className="text-2xl font-bold text-slate-800">Patient Registry</h2>
                    <p className="text-slate-500 text-sm">
                        Manage patient records and viewing history
                        {!isLoading && <span className="ml-2 text-sky-600 font-medium">({patients.length} patients)</span>}
                    </p>
                </div>

                <div className="flex gap-2">
                    <button
                        onClick={() => fetchPatients(searchQuery || undefined)}
                        className="bg-white hover:bg-slate-50 text-slate-700 px-4 py-2.5 rounded-lg flex items-center gap-2 font-medium border border-slate-200 transition-all hover:scale-105 active:scale-95"
                        title="Refresh patient list"
                    >
                        <RefreshCw size={18} />
                        Refresh
                    </button>

                    <button
                        onClick={() => setIsModalOpen(true)}
                        className="bg-sky-600 hover:bg-sky-700 text-white px-5 py-2.5 rounded-lg flex items-center gap-2 font-medium shadow-lg shadow-sky-200 transition-all hover:scale-105 active:scale-95"
                    >
                        <Plus size={20} />
                        Add New Patient
                    </button>
                </div>
            </div>

            {/* Error Message */}
            {error && (
                <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg flex items-start gap-3">
                    <AlertCircle size={20} className="flex-shrink-0 mt-0.5" />
                    <div>
                        <p className="font-medium">Error Loading Patients</p>
                        <p className="text-sm mt-1">{error}</p>
                    </div>
                </div>
            )}

            {/* Filter Bar */}
            <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm flex flex-col sm:flex-row gap-4">
                <div className="relative flex-1">
                    <Search size={20} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
                    <input
                        type="text"
                        placeholder="Search by Name..."
                        className="w-full pl-10 pr-4 py-2 rounded-lg border border-slate-200 focus:border-sky-500 focus:ring-2 focus:ring-sky-100 outline-none transition-all"
                        value={searchQuery}
                        onChange={(e) => setSearchQuery(e.target.value)}
                        disabled={isLoading}
                    />
                </div>
                <button className="flex items-center gap-2 px-4 py-2 border border-slate-200 rounded-lg text-slate-600 hover:bg-slate-50 font-medium">
                    <Filter size={18} />
                    Filters
                </button>
            </div>

            {/* Loading State */}
            {isLoading && (
                <div className="bg-white rounded-xl border border-slate-200 p-12 text-center">
                    <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-sky-600 mx-auto mb-4"></div>
                    <p className="text-slate-600 font-medium">Loading patients...</p>
                </div>
            )}

            {/* Empty State */}
            {!isLoading && !error && patients.length === 0 && (
                <div className="bg-white rounded-xl border border-slate-200 p-12 text-center">
                    <div className="text-slate-400 mb-4">
                        <svg className="w-16 h-16 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
                        </svg>
                    </div>
                    <h3 className="text-lg font-semibold text-slate-700 mb-2">No Patients Found</h3>
                    <p className="text-slate-500 mb-4">
                        {searchQuery ? 'Try a different search term' : 'Get started by adding your first patient'}
                    </p>
                    {!searchQuery && (
                        <button
                            onClick={() => setIsModalOpen(true)}
                            className="bg-sky-600 hover:bg-sky-700 text-white px-5 py-2.5 rounded-lg inline-flex items-center gap-2 font-medium"
                        >
                            <Plus size={20} />
                            Add First Patient
                        </button>
                    )}
                </div>
            )}

            {/* Table */}
            {!isLoading && !error && patients.length > 0 && (
                <DataTable
                    columns={columns}
                    data={patients}
                    onRowClick={(row) => console.log('Row clicked:', row)}
                />
            )}

            {/* Add Patient Modal */}
            <AddPatientModal
                isOpen={isModalOpen}
                onClose={() => setIsModalOpen(false)}
                onSave={handleAddPatient}
            />
        </div>
    )
}

