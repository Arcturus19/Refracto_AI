import React, { useEffect, useState, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import { Activity, Users, Image, TrendingUp, Bell } from 'lucide-react'
import { imagingService, type ImageRecord } from '../services/api'
import { toast } from 'sonner'

const Dashboard: React.FC = () => {
    const navigate = useNavigate()
    const [latestImageId, setLatestImageId] = useState<number | null>(null)
    const [pollingEnabled, setPollingEnabled] = useState(true)
    const [stats, setStats] = useState({
        totalPatients: 145,
        totalScans: 1234,
        pendingAnalysis: 23,
        accuracy: 94.5
    })

    // Poll for new images every 5 seconds
    useEffect(() => {
        if (!pollingEnabled) return

        const checkForNewImages = async () => {
            try {
                const recentImages = await imagingService.getRecentImages(1)

                if (recentImages && recentImages.length > 0) {
                    const newestImage = recentImages[0]

                    // Check if this is a new image
                    if (latestImageId !== null && newestImage.id !== latestImageId) {
                        // New image detected!
                        const imageType = newestImage.image_type === 'FUNDUS' ? 'Fundus' : 'OCT'

                        toast(
                            <>
                                <div className="flex items-start gap-3">
                                    <Bell className="text-blue-500 mt-1" size={20} />
                                    <div>
                                        <p className="font-semibold">New {imageType} Scan Received</p>
                                        <p className="text-sm text-gray-600">
                                            Patient ID: {newestImage.patient_id.slice(0, 8)}...
                                        </p>
                                        <p className="text-xs text-blue-600 mt-1">Click to analyze →</p>
                                    </div>
                                </div>
                            </>,
                            {
                                duration: 8000,
                                action: {
                                    label: 'Analyze',
                                    onClick: () => {
                                        // Navigate to analysis page
                                        navigate('/analysis')
                                    }
                                }
                            }
                        )
                    }

                    // Update latest image ID
                    setLatestImageId(newestImage.id)
                }
            } catch (error) {
                console.error('Error checking for new images:', error)
            }
        }

        // Initial check
        checkForNewImages()

        // Set up polling interval
        const intervalId = setInterval(checkForNewImages, 5000) // 5 seconds

        return () => clearInterval(intervalId)
    }, [latestImageId, pollingEnabled, navigate])

    return (
        <div className="p-6">
            {/* Header */}
            <div className="flex flex-col md:flex-row md:justify-between md:items-center mb-8 gap-4">
                <div>
                    <h1 className="text-3xl font-bold text-slate-900 tracking-tight">Dashboard Overview</h1>
                    <p className="text-slate-500 mt-1 font-medium">Welcome back! Here's your clinic's performance at a glance.</p>
                </div>

                {/* Polling Status */}
                <div className="flex items-center gap-2">
                    <div className={`w-2 h-2 rounded-full ${pollingEnabled ? 'bg-green-500 animate-pulse' : 'bg-gray-400'}`} />
                    <span className="text-sm text-gray-600">
                        {pollingEnabled ? 'Live updates active' : 'Updates paused'}
                    </span>
                    <button
                        onClick={() => setPollingEnabled(!pollingEnabled)}
                        className="ml-2 px-3 py-1 text-sm bg-gray-200 hover:bg-gray-300 rounded"
                    >
                        {pollingEnabled ? 'Pause' : 'Resume'}
                    </button>
                </div>
            </div>

            {/* Stats Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
                {/* Total Patients */}
                <div className="bg-white rounded-2xl premium-shadow p-6 transition-all duration-300 hover:-translate-y-1">
                    <div className="flex items-center justify-between">
                        <div>
                            <p className="text-slate-500 text-sm font-semibold tracking-wide uppercase">Total Patients</p>
                            <p className="text-3xl font-bold text-slate-800 mt-2">{stats.totalPatients}</p>
                            <p className="text-emerald-500 text-sm font-medium mt-2 flex items-center gap-1">↑ 12% <span className="text-slate-400 font-normal">from last month</span></p>
                        </div>
                        <div className="bg-gradient-to-br from-blue-50 to-blue-100 p-4 rounded-2xl">
                            <Users className="text-blue-600" size={24} />
                        </div>
                    </div>
                </div>

                {/* Total Scans */}
                <div className="bg-white rounded-2xl premium-shadow p-6 transition-all duration-300 hover:-translate-y-1">
                    <div className="flex items-center justify-between">
                        <div>
                            <p className="text-slate-500 text-sm font-semibold tracking-wide uppercase">Total Scans</p>
                            <p className="text-3xl font-bold text-slate-800 mt-2">{stats.totalScans}</p>
                            <p className="text-emerald-500 text-sm font-medium mt-2 flex items-center gap-1">↑ 8% <span className="text-slate-400 font-normal">from last month</span></p>
                        </div>
                        <div className="bg-gradient-to-br from-purple-50 to-purple-100 p-4 rounded-2xl">
                            <Image className="text-purple-600" size={24} />
                        </div>
                    </div>
                </div>

                {/* Pending Analysis */}
                <div className="bg-white rounded-2xl premium-shadow p-6 transition-all duration-300 hover:-translate-y-1">
                    <div className="flex items-center justify-between">
                        <div>
                            <p className="text-slate-500 text-sm font-semibold tracking-wide uppercase">Pending Analysis</p>
                            <p className="text-3xl font-bold text-slate-800 mt-2">{stats.pendingAnalysis}</p>
                            <p className="text-rose-500 text-sm font-medium mt-2 flex items-center gap-1">Requires attention</p>
                        </div>
                        <div className="bg-gradient-to-br from-rose-50 to-rose-100 p-4 rounded-2xl">
                            <Activity className="text-rose-600" size={24} />
                        </div>
                    </div>
                </div>

                {/* AI Accuracy */}
                <div className="bg-white rounded-2xl premium-shadow p-6 transition-all duration-300 hover:-translate-y-1">
                    <div className="flex items-center justify-between">
                        <div>
                            <p className="text-slate-500 text-sm font-semibold tracking-wide uppercase">AI Accuracy</p>
                            <p className="text-3xl font-bold text-slate-800 mt-2">{stats.accuracy}%</p>
                            <p className="text-emerald-500 text-sm font-medium mt-2 flex items-center gap-1">Excellent range</p>
                        </div>
                        <div className="bg-gradient-to-br from-emerald-50 to-emerald-100 p-4 rounded-2xl">
                            <TrendingUp className="text-emerald-600" size={24} />
                        </div>
                    </div>
                </div>
            </div>

            {/* Recent Activity */}
            <div className="bg-white rounded-2xl premium-shadow p-6 md:p-8">
                <div className="flex justify-between items-center mb-6">
                    <h2 className="text-xl font-bold text-slate-800 tracking-tight">Recent Activity</h2>
                    <button className="text-sm font-medium text-sky-600 hover:text-sky-700 transition-colors">View All</button>
                </div>
                
                <div className="space-y-3">
                    <div className="flex items-center justify-between p-4 bg-slate-50/50 border border-slate-100 rounded-2xl hover:bg-slate-50 transition-colors group">
                        <div className="flex items-center gap-4">
                            <div className="bg-blue-100/50 p-2.5 rounded-xl border border-blue-100">
                                <Image className="text-blue-600" size={20} />
                            </div>
                            <div>
                                <p className="font-semibold text-slate-800">New fundus scan uploaded</p>
                                <p className="text-sm text-slate-500 font-medium">Patient: John Doe • <span className="text-slate-400">5 minutes ago</span></p>
                            </div>
                        </div>
                        <button
                            onClick={() => navigate('/analysis')}
                            className="px-5 py-2.5 bg-sky-600 text-white font-medium text-sm rounded-xl hover:bg-sky-700 transition-all duration-200 transform active:scale-95 shadow-sm shadow-sky-600/20"
                        >
                            Analyze
                        </button>
                    </div>

                    <div className="flex items-center justify-between p-4 bg-slate-50/50 border border-slate-100 rounded-2xl hover:bg-slate-50 transition-colors group">
                        <div className="flex items-center gap-4">
                            <div className="bg-emerald-100/50 p-2.5 rounded-xl border border-emerald-100">
                                <Activity className="text-emerald-600" size={20} />
                            </div>
                            <div>
                                <p className="font-semibold text-slate-800">AI analysis completed</p>
                                <p className="text-sm text-slate-500 font-medium">Patient: Jane Smith • <span className="text-slate-400">15 minutes ago</span></p>
                            </div>
                        </div>
                        <button
                            onClick={() => navigate('/patients')}
                            className="px-5 py-2.5 bg-white border border-slate-200 text-slate-700 font-medium text-sm rounded-xl hover:bg-slate-50 hover:border-slate-300 transition-all duration-200 transform active:scale-95"
                        >
                            View Results
                        </button>
                    </div>

                    <div className="flex items-center justify-between p-4 bg-slate-50/50 border border-slate-100 rounded-2xl hover:bg-slate-50 transition-colors group">
                        <div className="flex items-center gap-4">
                            <div className="bg-purple-100/50 p-2.5 rounded-xl border border-purple-100">
                                <Users className="text-purple-600" size={20} />
                            </div>
                            <div>
                                <p className="font-semibold text-slate-800">New patient registered</p>
                                <p className="text-sm text-slate-500 font-medium">Patient: Bob Wilson • <span className="text-slate-400">1 hour ago</span></p>
                            </div>
                        </div>
                        <button
                            onClick={() => navigate('/patients')}
                            className="px-5 py-2.5 bg-white border border-slate-200 text-slate-700 font-medium text-sm rounded-xl hover:bg-slate-50 hover:border-slate-300 transition-all duration-200 transform active:scale-95"
                        >
                            View Profile
                        </button>
                    </div>
                </div>
            </div>
        </div>
    )
}

export default Dashboard
