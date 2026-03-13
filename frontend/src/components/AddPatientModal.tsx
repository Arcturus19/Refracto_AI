import React, { useState } from 'react'
import { X, Save, User, Calendar, Phone } from 'lucide-react'

interface AddPatientModalProps {
    isOpen: boolean
    onClose: () => void
    onSave: (patientData: any) => void
}

export default function AddPatientModal({ isOpen, onClose, onSave }: AddPatientModalProps) {
    const [formData, setFormData] = useState({
        name: '',
        dob: '',
        contact: '',
        gender: 'Male'
    })

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault()
        onSave(formData)
        onClose()
        setFormData({ name: '', dob: '', contact: '', gender: 'Male' }) // Reset
    }

    if (!isOpen) return null

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
            {/* Backdrop */}
            <div
                className="absolute inset-0 bg-slate-900/60 backdrop-blur-sm transition-opacity"
                onClick={onClose}
            />

            {/* Modal Content */}
            <div className="relative w-full max-w-lg bg-white rounded-3xl shadow-2xl premium-shadow transform transition-all animate-scale-up border border-slate-100/50 overflow-hidden">
                <div className="px-7 py-5 bg-slate-50/50 border-b border-slate-100 flex items-center justify-between">
                    <h2 className="text-xl font-bold tracking-tight text-slate-800 flex items-center gap-2">
                        <div className="p-1.5 bg-sky-100 text-sky-600 rounded-lg">
                            <User size={18} />
                        </div>
                        Add New Patient
                    </h2>
                    <button onClick={onClose} className="p-2 hover:bg-slate-200 rounded-full text-slate-400 hover:text-slate-600 transition-colors bg-white shadow-sm border border-slate-100">
                        <X size={18} />
                    </button>
                </div>

                <form onSubmit={handleSubmit} className="p-7 space-y-5">
                    {/* Name */}
                    <div>
                        <label className="block text-sm font-semibold text-slate-700 mb-1.5">Full Name</label>
                        <div className="relative">
                            <User size={18} className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-400" />
                            <input
                                type="text"
                                required
                                className="w-full pl-11 pr-4 py-3 rounded-xl border border-slate-200 focus:border-sky-500 focus:ring-4 focus:ring-sky-500/10 outline-none transition-all text-slate-800 font-medium placeholder:font-normal shadow-sm"
                                placeholder="e.g. John Doe"
                                value={formData.name}
                                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                            />
                        </div>
                    </div>

                    <div className="grid grid-cols-2 gap-5">
                        {/* DOB */}
                        <div>
                            <label className="block text-sm font-semibold text-slate-700 mb-1.5">Date of Birth</label>
                            <div className="relative">
                                <Calendar size={18} className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-400" />
                                <input
                                    type="date"
                                    required
                                    className="w-full pl-11 pr-4 py-3 rounded-xl border border-slate-200 focus:border-sky-500 focus:ring-4 focus:ring-sky-500/10 outline-none transition-all text-slate-800 font-medium shadow-sm"
                                    value={formData.dob}
                                    onChange={(e) => setFormData({ ...formData, dob: e.target.value })}
                                />
                            </div>
                        </div>

                        {/* Gender */}
                        <div>
                            <label className="block text-sm font-semibold text-slate-700 mb-1.5">Gender</label>
                            <select
                                className="w-full px-4 py-3 rounded-xl border border-slate-200 focus:border-sky-500 focus:ring-4 focus:ring-sky-500/10 outline-none transition-all bg-white text-slate-800 font-medium shadow-sm"
                                value={formData.gender}
                                onChange={(e) => setFormData({ ...formData, gender: e.target.value })}
                            >
                                <option value="Male">Male</option>
                                <option value="Female">Female</option>
                                <option value="Other">Other</option>
                            </select>
                        </div>
                    </div>

                    {/* Contact */}
                    <div>
                        <label className="block text-sm font-semibold text-slate-700 mb-1.5">Contact Number</label>
                        <div className="relative">
                            <Phone size={18} className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-400" />
                            <input
                                type="tel"
                                required
                                className="w-full pl-11 pr-4 py-3 rounded-xl border border-slate-200 focus:border-sky-500 focus:ring-4 focus:ring-sky-500/10 outline-none transition-all text-slate-800 font-medium placeholder:font-normal shadow-sm"
                                placeholder="+1 234 567 890"
                                value={formData.contact}
                                onChange={(e) => setFormData({ ...formData, contact: e.target.value })}
                            />
                        </div>
                    </div>

                    {/* Actions */}
                    <div className="pt-4 flex items-center justify-end gap-3 text-sm">
                        <button
                            type="button"
                            onClick={onClose}
                            className="px-5 py-2.5 font-bold text-slate-600 bg-slate-100 hover:bg-slate-200 rounded-xl transition-all active:scale-95"
                        >
                            Cancel
                        </button>
                        <button
                            type="submit"
                            className="px-6 py-2.5 font-bold bg-sky-600 hover:bg-sky-700 text-white rounded-xl shadow-lg shadow-sky-600/20 hover:-translate-y-0.5 transition-all active:scale-95 flex items-center gap-2"
                        >
                            <Save size={18} />
                            Save Patient
                        </button>
                    </div>
                </form>
            </div>
        </div>
    )
}
