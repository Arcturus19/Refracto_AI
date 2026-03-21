import React, { useEffect, useState } from 'react'
import {
  Bell,
  Shield,
  Eye,
  Save,
  Monitor,
  Moon,
  Sun,
  Database,
  RefreshCw,
} from 'lucide-react'
import { toast } from 'sonner'
import { authService } from '../services/api'

interface SettingsState {
  notifications: {
    newScans: boolean
    highRiskAlerts: boolean
    weeklySummary: boolean
    emailNotifications: boolean
  }
  analysis: {
    autoRefreshDashboard: boolean
    defaultConfidenceThreshold: number
    showClinicalHints: boolean
  }
  privacy: {
    blurPatientIdentifiers: boolean
    requireConfirmForExports: boolean
  }
  appearance: {
    density: 'comfortable' | 'compact'
    colorMode: 'system' | 'light' | 'dark'
  }
}

const initialSettings: SettingsState = {
  notifications: {
    newScans: true,
    highRiskAlerts: true,
    weeklySummary: true,
    emailNotifications: false,
  },
  analysis: {
    autoRefreshDashboard: true,
    defaultConfidenceThreshold: 70,
    showClinicalHints: true,
  },
  privacy: {
    blurPatientIdentifiers: false,
    requireConfirmForExports: true,
  },
  appearance: {
    density: 'comfortable',
    colorMode: 'system',
  },
}

function Toggle({ checked, onChange }: { checked: boolean; onChange: () => void }) {
  return (
    <button
      type="button"
      onClick={onChange}
      className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${checked ? 'bg-sky-600' : 'bg-slate-300'}`}
      aria-pressed={checked}
    >
      <span
        className={`inline-block h-5 w-5 transform rounded-full bg-white transition-transform ${checked ? 'translate-x-5' : 'translate-x-1'}`}
      />
    </button>
  )
}

export default function SettingsPage() {
  const [settings, setSettings] = useState<SettingsState>(initialSettings)
  const [isSaving, setIsSaving] = useState(false)

  useEffect(() => {
    const loadSettings = async () => {
      try {
        const response = await authService.getMySettings()
        const parsed = (response?.settings || {}) as Partial<SettingsState>
        setSettings((prev) => ({
          ...prev,
          ...parsed,
          notifications: { ...prev.notifications, ...(parsed.notifications || {}) },
          analysis: { ...prev.analysis, ...(parsed.analysis || {}) },
          privacy: { ...prev.privacy, ...(parsed.privacy || {}) },
          appearance: { ...prev.appearance, ...(parsed.appearance || {}) },
        }))
      } catch {
        const raw = localStorage.getItem('app_settings')
        if (!raw) return
        try {
          const parsed = JSON.parse(raw) as Partial<SettingsState>
          setSettings((prev) => ({
            ...prev,
            ...parsed,
            notifications: { ...prev.notifications, ...(parsed.notifications || {}) },
            analysis: { ...prev.analysis, ...(parsed.analysis || {}) },
            privacy: { ...prev.privacy, ...(parsed.privacy || {}) },
            appearance: { ...prev.appearance, ...(parsed.appearance || {}) },
          }))
        } catch {
          // Ignore malformed local settings and continue with defaults.
        }
      }
    }

    loadSettings()
  }, [])

  const saveSettings = async () => {
    try {
      setIsSaving(true)
      await authService.updateMySettings(settings)
      localStorage.setItem('app_settings', JSON.stringify(settings))
      toast.success('Settings saved successfully')
    } catch {
      localStorage.setItem('app_settings', JSON.stringify(settings))
      toast.success('Settings saved locally (backend unavailable)')
    } finally {
      setIsSaving(false)
    }
  }

  const resetSettings = () => {
    setSettings(initialSettings)
    localStorage.removeItem('app_settings')
    toast.success('Settings reset to defaults')
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold text-slate-900 tracking-tight">Settings</h1>
          <p className="text-slate-500 mt-1">Configure notifications, privacy, analysis preferences, and appearance.</p>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={resetSettings}
            className="inline-flex items-center gap-2 px-4 py-2.5 rounded-xl bg-white border border-slate-200 text-slate-700 font-semibold hover:bg-slate-50"
          >
            Reset
          </button>
          <button
            onClick={saveSettings}
            disabled={isSaving}
            className="inline-flex items-center gap-2 px-4 py-2.5 rounded-xl bg-sky-600 text-white font-semibold hover:bg-sky-700 disabled:opacity-60"
          >
            {isSaving ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Save className="w-4 h-4" />}
            {isSaving ? 'Saving...' : 'Save Settings'}
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
        <div className="xl:col-span-2 space-y-6">
          <section className="bg-white rounded-2xl premium-shadow p-6">
            <div className="flex items-center gap-2 mb-4">
              <Bell className="w-5 h-5 text-sky-600" />
              <h2 className="text-lg font-bold text-slate-800">Notifications</h2>
            </div>
            <div className="space-y-4">
              {[
                ['newScans', 'New scan received alerts'],
                ['highRiskAlerts', 'High-risk pathology alerts'],
                ['weeklySummary', 'Weekly operational summary'],
                ['emailNotifications', 'Email notifications'],
              ].map(([key, label]) => (
                <div key={key} className="flex items-center justify-between border border-slate-100 rounded-xl p-3">
                  <span className="text-sm text-slate-700 font-medium">{label}</span>
                  <Toggle
                    checked={settings.notifications[key as keyof SettingsState['notifications']]}
                    onChange={() =>
                      setSettings((prev) => ({
                        ...prev,
                        notifications: {
                          ...prev.notifications,
                          [key]: !prev.notifications[key as keyof SettingsState['notifications']],
                        },
                      }))
                    }
                  />
                </div>
              ))}
            </div>
          </section>

          <section className="bg-white rounded-2xl premium-shadow p-6">
            <div className="flex items-center gap-2 mb-4">
              <Database className="w-5 h-5 text-indigo-600" />
              <h2 className="text-lg font-bold text-slate-800">Analysis Preferences</h2>
            </div>
            <div className="space-y-4">
              <div className="flex items-center justify-between border border-slate-100 rounded-xl p-3">
                <span className="text-sm text-slate-700 font-medium">Auto-refresh dashboard statistics</span>
                <Toggle
                  checked={settings.analysis.autoRefreshDashboard}
                  onChange={() =>
                    setSettings((prev) => ({
                      ...prev,
                      analysis: {
                        ...prev.analysis,
                        autoRefreshDashboard: !prev.analysis.autoRefreshDashboard,
                      },
                    }))
                  }
                />
              </div>

              <div className="border border-slate-100 rounded-xl p-4">
                <label className="text-sm text-slate-700 font-medium">Default confidence threshold: {settings.analysis.defaultConfidenceThreshold}%</label>
                <input
                  type="range"
                  min={50}
                  max={95}
                  step={1}
                  value={settings.analysis.defaultConfidenceThreshold}
                  onChange={(e) =>
                    setSettings((prev) => ({
                      ...prev,
                      analysis: {
                        ...prev.analysis,
                        defaultConfidenceThreshold: Number(e.target.value),
                      },
                    }))
                  }
                  className="w-full mt-3"
                />
              </div>

              <div className="flex items-center justify-between border border-slate-100 rounded-xl p-3">
                <span className="text-sm text-slate-700 font-medium">Show clinical hints in analysis views</span>
                <Toggle
                  checked={settings.analysis.showClinicalHints}
                  onChange={() =>
                    setSettings((prev) => ({
                      ...prev,
                      analysis: {
                        ...prev.analysis,
                        showClinicalHints: !prev.analysis.showClinicalHints,
                      },
                    }))
                  }
                />
              </div>
            </div>
          </section>
        </div>

        <div className="space-y-6">
          <section className="bg-white rounded-2xl premium-shadow p-6">
            <div className="flex items-center gap-2 mb-4">
              <Shield className="w-5 h-5 text-rose-600" />
              <h2 className="text-lg font-bold text-slate-800">Privacy</h2>
            </div>
            <div className="space-y-4">
              <div className="flex items-center justify-between border border-slate-100 rounded-xl p-3">
                <span className="text-sm text-slate-700 font-medium">Blur patient identifiers</span>
                <Toggle
                  checked={settings.privacy.blurPatientIdentifiers}
                  onChange={() =>
                    setSettings((prev) => ({
                      ...prev,
                      privacy: {
                        ...prev.privacy,
                        blurPatientIdentifiers: !prev.privacy.blurPatientIdentifiers,
                      },
                    }))
                  }
                />
              </div>

              <div className="flex items-center justify-between border border-slate-100 rounded-xl p-3">
                <span className="text-sm text-slate-700 font-medium">Confirm before report exports</span>
                <Toggle
                  checked={settings.privacy.requireConfirmForExports}
                  onChange={() =>
                    setSettings((prev) => ({
                      ...prev,
                      privacy: {
                        ...prev.privacy,
                        requireConfirmForExports: !prev.privacy.requireConfirmForExports,
                      },
                    }))
                  }
                />
              </div>
            </div>
          </section>

          <section className="bg-white rounded-2xl premium-shadow p-6">
            <div className="flex items-center gap-2 mb-4">
              <Eye className="w-5 h-5 text-emerald-600" />
              <h2 className="text-lg font-bold text-slate-800">Appearance</h2>
            </div>

            <div className="space-y-3">
              <div>
                <label className="text-xs font-semibold uppercase tracking-wide text-slate-500">Density</label>
                <div className="mt-2 flex gap-2">
                  {(['comfortable', 'compact'] as const).map((mode) => (
                    <button
                      key={mode}
                      onClick={() => setSettings((prev) => ({ ...prev, appearance: { ...prev.appearance, density: mode } }))}
                      className={`flex-1 px-3 py-2 rounded-lg text-sm font-semibold border ${settings.appearance.density === mode ? 'bg-sky-50 text-sky-700 border-sky-200' : 'bg-white text-slate-600 border-slate-200 hover:border-slate-300'}`}
                    >
                      {mode}
                    </button>
                  ))}
                </div>
              </div>

              <div>
                <label className="text-xs font-semibold uppercase tracking-wide text-slate-500">Color Mode</label>
                <div className="mt-2 grid grid-cols-3 gap-2">
                  {[
                    { key: 'system', label: 'System', icon: Monitor },
                    { key: 'light', label: 'Light', icon: Sun },
                    { key: 'dark', label: 'Dark', icon: Moon },
                  ].map((mode) => (
                    <button
                      key={mode.key}
                      onClick={() =>
                        setSettings((prev) => ({
                          ...prev,
                          appearance: { ...prev.appearance, colorMode: mode.key as SettingsState['appearance']['colorMode'] },
                        }))
                      }
                      className={`px-3 py-2 rounded-lg text-xs font-semibold border flex items-center justify-center gap-1.5 ${settings.appearance.colorMode === mode.key ? 'bg-sky-50 text-sky-700 border-sky-200' : 'bg-white text-slate-600 border-slate-200 hover:border-slate-300'}`}
                    >
                      <mode.icon className="w-3.5 h-3.5" />
                      {mode.label}
                    </button>
                  ))}
                </div>
              </div>
            </div>
          </section>
        </div>
      </div>
    </div>
  )
}
