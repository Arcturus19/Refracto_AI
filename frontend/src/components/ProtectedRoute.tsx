import React, { useEffect } from 'react'
import { Navigate } from 'react-router-dom'
import { useAuthStore } from '../store/useAuthStore'
import { Loader2 } from 'lucide-react'

interface ProtectedRouteProps {
    children: React.ReactNode
}

export default function ProtectedRoute({ children }: ProtectedRouteProps) {
    const { isAuthenticated, isLoading, hasCheckedAuth, checkAuth } = useAuthStore()

    useEffect(() => {
        if (!hasCheckedAuth && !isLoading) {
            void checkAuth()
        }
    }, [hasCheckedAuth, isLoading, checkAuth])

    // Show spinner while validating token
    if (!hasCheckedAuth || isLoading) {
        return (
            <div className="min-h-screen flex items-center justify-center bg-slate-50">
                <div className="flex flex-col items-center gap-3">
                    <Loader2 className="animate-spin text-blue-500" size={32} />
                    <p className="text-slate-500 text-sm font-medium">Authenticating...</p>
                </div>
            </div>
        )
    }

    // No token at all — redirect to login
    if (!isAuthenticated) {
        return <Navigate to="/login" replace />
    }

    return <>{children}</>
}
