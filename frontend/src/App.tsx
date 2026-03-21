import React, { useEffect } from 'react'
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom'
import { Toaster } from 'sonner'
import MainLayout from './layouts/MainLayout'
import Dashboard from './pages/Dashboard'
import AnalysisPage from './pages/AnalysisPage'
import PatientList from './pages/PatientList'
import PatientDetails from './pages/PatientDetails'
import LoginPage from './pages/LoginPage'
import ReportsPage from './pages/ReportsPage'
import SettingsPage from './pages/SettingsPage'
import ProfilePage from './pages/ProfilePage'
import ScansPage from './pages/ScansPage'
import ScanDetailsPage from './pages/ScanDetailsPage'
import AuditPage from './pages/AuditPage'
import SystemStatusPage from './pages/SystemStatusPage'
import UserManagementPage from './pages/UserManagementPage'
import ErrorBoundary from './components/ErrorBoundary'
import ProtectedRoute from './components/ProtectedRoute'
import { useAuthStore } from './store/useAuthStore'
import { AUTH_EXPIRED_EVENT } from './services/api'

export default function App() {
  const { checkAuth, clearSession } = useAuthStore()

  // On app mount: validate any stored token with the backend
  useEffect(() => {
    void checkAuth()

    const handleExpiredSession = () => {
      clearSession()
    }

    window.addEventListener(AUTH_EXPIRED_EVENT, handleExpiredSession)
    return () => window.removeEventListener(AUTH_EXPIRED_EVENT, handleExpiredSession)
  }, [checkAuth, clearSession])

  return (
    <Router>
      <Toaster position="top-right" richColors />
      <ErrorBoundary>
        <Routes>
          {/* Public route */}
          <Route path="/login" element={<LoginPage />} />

          {/* Protected routes - all wrapped in MainLayout */}
          <Route
            path="/"
            element={
              <ProtectedRoute>
                <MainLayout>
                  <Dashboard />
                </MainLayout>
              </ProtectedRoute>
            }
          />
          <Route
            path="/analysis"
            element={
              <ProtectedRoute>
                <MainLayout>
                  <AnalysisPage />
                </MainLayout>
              </ProtectedRoute>
            }
          />
          <Route
            path="/scans"
            element={
              <ProtectedRoute>
                <MainLayout>
                  <ScansPage />
                </MainLayout>
              </ProtectedRoute>
            }
          />
          <Route
            path="/scans/:imageId"
            element={
              <ProtectedRoute>
                <MainLayout>
                  <ScanDetailsPage />
                </MainLayout>
              </ProtectedRoute>
            }
          />
          <Route
            path="/patients"
            element={
              <ProtectedRoute>
                <MainLayout>
                  <PatientList />
                </MainLayout>
              </ProtectedRoute>
            }
          />
          <Route
            path="/patients/:id"
            element={
              <ProtectedRoute>
                <MainLayout>
                  <PatientDetails />
                </MainLayout>
              </ProtectedRoute>
            }
          />
          <Route
            path="/reports"
            element={
              <ProtectedRoute>
                <MainLayout>
                  <ReportsPage />
                </MainLayout>
              </ProtectedRoute>
            }
          />
          <Route
            path="/audit"
            element={
              <ProtectedRoute>
                <MainLayout>
                  <AuditPage />
                </MainLayout>
              </ProtectedRoute>
            }
          />
          <Route
            path="/system"
            element={
              <ProtectedRoute>
                <MainLayout>
                  <SystemStatusPage />
                </MainLayout>
              </ProtectedRoute>
            }
          />
          <Route
            path="/admin/users"
            element={
              <ProtectedRoute>
                <MainLayout>
                  <UserManagementPage />
                </MainLayout>
              </ProtectedRoute>
            }
          />
          <Route
            path="/settings"
            element={
              <ProtectedRoute>
                <MainLayout>
                  <SettingsPage />
                </MainLayout>
              </ProtectedRoute>
            }
          />
          <Route
            path="/profile"
            element={
              <ProtectedRoute>
                <MainLayout>
                  <ProfilePage />
                </MainLayout>
              </ProtectedRoute>
            }
          />

          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </ErrorBoundary>
    </Router>
  )
}
