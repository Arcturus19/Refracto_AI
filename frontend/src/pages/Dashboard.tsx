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
            <div className="flex justify-between items-center mb-6">
                <div>
                    <h1 className="text-3xl font-bold text-gray-900">Dashboard</h1>
                    <p className="text-gray-600 mt-1">Welcome back! Here's your overview.</p>
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
                <div className="bg-white rounded-lg shadow p-6 border-l-4 border-blue-500">
                    <div className="flex items-center justify-between">
                        <div>
                            <p className="text-gray-600 text-sm font-medium">Total Patients</p>
                            <p className="text-3xl font-bold text-gray-900 mt-2">{stats.totalPatients}</p>
                            <p className="text-green-600 text-sm mt-2">↑ 12% from last month</p>
                        </div>
                        <div className="bg-blue-100 p-3 rounded-full">
                            <Users className="text-blue-600" size={24} />
                        </div>
                    </div>
                </div>

                {/* Total Scans */}
                <div className="bg-white rounded-lg shadow p-6 border-l-4 border-purple-500">
                    <div className="flex items-center justify-between">
                        <div>
                            <p className="text-gray-600 text-sm font-medium">Total Scans</p>
                            <p className="text-3xl font-bold text-gray-900 mt-2">{stats.totalScans}</p>
                            <p className="text-green-600 text-sm mt-2">↑ 8% from last month</p>
                        </div>
                        <div className="bg-purple-100 p-3 rounded-full">
                            <Image className="text-purple-600" size={24} />
                        </div>
                    </div>
                </div>

                {/* Pending Analysis */}
                <div className="bg-white rounded-lg shadow p-6 border-l-4 border-orange-500">
                    <div className="flex items-center justify-between">
                        <div>
                            <p className="text-gray-600 text-sm font-medium">Pending Analysis</p>
                            <p className="text-3xl font-bold text-gray-900 mt-2">{stats.pendingAnalysis}</p>
                            <p className="text-orange-600 text-sm mt-2">Requires attention</p>
                        </div>
                        <div className="bg-orange-100 p-3 rounded-full">
                            <Activity className="text-orange-600" size={24} />
                        </div>
                    </div>
                </div>

                {/* AI Accuracy */}
                <div className="bg-white rounded-lg shadow p-6 border-l-4 border-green-500">
                    <div className="flex items-center justify-between">
                        <div>
                            <p className="text-gray-600 text-sm font-medium">AI Accuracy</p>
                            <p className="text-3xl font-bold text-gray-900 mt-2">{stats.accuracy}%</p>
                            <p className="text-green-600 text-sm mt-2">Excellent performance</p>
                        </div>
                        <div className="bg-green-100 p-3 rounded-full">
                            <TrendingUp className="text-green-600" size={24} />
                        </div>
                    </div>
                </div>
            </div>

            {/* Recent Activity */}
            <div className="bg-white rounded-lg shadow p-6">
                <h2 className="text-xl font-bold text-gray-900 mb-4">Recent Activity</h2>
                <div className="space-y-4">
                    <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
                        <div className="flex items-center gap-3">
                            <div className="bg-blue-100 p-2 rounded-full">
                                <Image className="text-blue-600" size={20} />
                            </div>
                            <div>
                                <p className="font-medium text-gray-900">New fundus scan uploaded</p>
                                <p className="text-sm text-gray-600">Patient: John Doe • 5 minutes ago</p>
                            </div>
                        </div>
                        <button
                            onClick={() => navigate('/analysis')}
                            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
                        >
                            Analyze
                        </button>
                    </div>

                    <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
                        <div className="flex items-center gap-3">
                            <div className="bg-green-100 p-2 rounded-full">
                                <Activity className="text-green-600" size={20} />
                            </div>
                            <div>
                                <p className="font-medium text-gray-900">AI analysis completed</p>
                                <p className="text-sm text-gray-600">Patient: Jane Smith • 15 minutes ago</p>
                            </div>
                        </div>
                        <button
                            onClick={() => navigate('/patients')}
                            className="px-4 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300"
                        >
                            View
                        </button>
                    </div>

                    <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
                        <div className="flex items-center gap-3">
                            <div className="bg-purple-100 p-2 rounded-full">
                                <Users className="text-purple-600" size={20} />
                            </div>
                            <div>
                                <p className="font-medium text-gray-900">New patient registered</p>
                                <p className="text-sm text-gray-600">Patient: Bob Wilson • 1 hour ago</p>
                            </div>
                        </div>
                        <button
                            onClick={() => navigate('/patients')}
                            className="px-4 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300"
                        >
                            View
                        </button>
                    </div>
                </div>
            </div>
        </div>
    )
}

export default Dashboard
