import React, { useEffect } from 'react'
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom'
import { Toaster } from 'sonner'
import MainLayout from './layouts/MainLayout'
import Dashboard from './pages/Dashboard'
import AnalysisPage from './pages/AnalysisPage'
import PatientList from './pages/PatientList'
import LoginPage from './pages/LoginPage'
import ProtectedRoute from './components/ProtectedRoute'
import { useAuthStore } from './store/useAuthStore'

export default function App() {
  const { checkAuth } = useAuthStore()

  // On app mount: validate any stored token with the backend
  useEffect(() => {
    checkAuth()
  }, [])

  return (
    <Router>
      <Toaster position="top-right" richColors />
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
          path="/patients"
          element={
            <ProtectedRoute>
              <MainLayout>
                <PatientList />
              </MainLayout>
            </ProtectedRoute>
          }
        />

        {/* Catch-all: redirect unknown paths to home */}
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </Router>
  )
}
