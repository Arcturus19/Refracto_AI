import React, { useEffect, useMemo, useState } from 'react'
import { User, Mail, Shield, Calendar, Save, Camera, KeyRound } from 'lucide-react'
import { toast } from 'sonner'
import { useAuthStore } from '../store/useAuthStore'
import { authService } from '../services/api'

export default function ProfilePage() {
  const { user, updateUser } = useAuthStore()

  const [form, setForm] = useState({
    fullName: user?.full_name || '',
    email: user?.email || '',
    phone: '',
    department: user?.role === 'admin' ? 'Administration' : 'Ophthalmology',
    bio: 'Specialist in retinal screening and AI-assisted diagnosis.',
  })

  const [passwordForm, setPasswordForm] = useState({
    currentPassword: '',
    newPassword: '',
    confirmPassword: '',
  })

  useEffect(() => {
    if (!user) return
    setForm((prev) => ({
      ...prev,
      fullName: user.full_name || '',
      email: user.email || '',
      department: user.role === 'admin' ? 'Administration' : 'Ophthalmology',
    }))
  }, [user])

  const initials = useMemo(() => {
    if (!form.fullName.trim()) return 'RX'
    return form.fullName
      .split(' ')
      .map((n) => n[0])
      .join('')
      .slice(0, 2)
      .toUpperCase()
  }, [form.fullName])

  const saveProfile = async () => {
    try {
      const updated = await authService.updateProfile({
        full_name: form.fullName,
        email: form.email,
      })

      updateUser({
        full_name: updated.full_name,
        email: updated.email,
        updated_at: updated.updated_at,
      })

      toast.success('Profile changes saved')
    } catch (error: any) {
      const detail = error?.response?.data?.detail
      toast.error(detail || 'Failed to save profile changes')
    }
  }

  const updatePassword = async () => {
    if (!passwordForm.currentPassword || !passwordForm.newPassword || !passwordForm.confirmPassword) {
      toast.error('Please fill all password fields')
      return
    }

    if (passwordForm.newPassword !== passwordForm.confirmPassword) {
      toast.error('New password and confirmation do not match')
      return
    }

    if (passwordForm.newPassword.length < 8) {
      toast.error('New password must be at least 8 characters')
      return
    }

    try {
      await authService.changePassword({
        current_password: passwordForm.currentPassword,
        new_password: passwordForm.newPassword,
      })
      setPasswordForm({ currentPassword: '', newPassword: '', confirmPassword: '' })
      toast.success('Password updated successfully')
    } catch (error: any) {
      const detail = error?.response?.data?.detail
      toast.error(detail || 'Failed to update password')
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-slate-900 tracking-tight">My Profile</h1>
        <p className="text-slate-500 mt-1">Manage your account details and security settings.</p>
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
        <section className="bg-white rounded-2xl premium-shadow p-6 xl:col-span-1">
          <div className="flex flex-col items-center text-center">
            <div className="w-24 h-24 rounded-full bg-gradient-to-br from-sky-400 to-blue-600 text-white flex items-center justify-center text-2xl font-bold shadow-md">
              {initials}
            </div>
            <h2 className="mt-4 text-xl font-bold text-slate-800">{form.fullName || 'Unnamed User'}</h2>
            <p className="text-sm text-slate-500 capitalize">{user?.role || 'doctor'}</p>

            <button className="mt-4 inline-flex items-center gap-2 px-3 py-2 text-sm font-medium text-slate-700 bg-slate-100 hover:bg-slate-200 rounded-lg">
              <Camera className="w-4 h-4" />
              Change Avatar
            </button>
          </div>

          <div className="mt-6 pt-6 border-t border-slate-100 space-y-3 text-sm">
            <div className="flex items-start gap-2 text-slate-600">
              <Mail className="w-4 h-4 mt-0.5" />
              <span>{form.email || 'No email available'}</span>
            </div>
            <div className="flex items-start gap-2 text-slate-600">
              <Shield className="w-4 h-4 mt-0.5" />
              <span className="capitalize">Role: {user?.role || 'doctor'}</span>
            </div>
            <div className="flex items-start gap-2 text-slate-600">
              <Calendar className="w-4 h-4 mt-0.5" />
              <span>Member since {user?.created_at ? new Date(user.created_at).toLocaleDateString() : 'N/A'}</span>
            </div>
          </div>
        </section>

        <div className="xl:col-span-2 space-y-6">
          <section className="bg-white rounded-2xl premium-shadow p-6">
            <div className="flex items-center gap-2 mb-4">
              <User className="w-5 h-5 text-sky-600" />
              <h2 className="text-lg font-bold text-slate-800">Personal Information</h2>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="md:col-span-2">
                <label className="text-sm font-medium text-slate-700">Full Name</label>
                <input
                  type="text"
                  value={form.fullName}
                  onChange={(e) => setForm((prev) => ({ ...prev, fullName: e.target.value }))}
                  className="mt-1.5 w-full px-3 py-2.5 rounded-xl border border-slate-200 focus:border-sky-400 focus:ring-2 focus:ring-sky-100 outline-none"
                />
              </div>

              <div>
                <label className="text-sm font-medium text-slate-700">Email</label>
                <input
                  type="email"
                  value={form.email}
                  onChange={(e) => setForm((prev) => ({ ...prev, email: e.target.value }))}
                  className="mt-1.5 w-full px-3 py-2.5 rounded-xl border border-slate-200 focus:border-sky-400 focus:ring-2 focus:ring-sky-100 outline-none"
                />
              </div>

              <div>
                <label className="text-sm font-medium text-slate-700">Phone</label>
                <input
                  type="tel"
                  value={form.phone}
                  onChange={(e) => setForm((prev) => ({ ...prev, phone: e.target.value }))}
                  placeholder="Optional"
                  className="mt-1.5 w-full px-3 py-2.5 rounded-xl border border-slate-200 focus:border-sky-400 focus:ring-2 focus:ring-sky-100 outline-none"
                />
              </div>

              <div>
                <label className="text-sm font-medium text-slate-700">Department</label>
                <input
                  type="text"
                  value={form.department}
                  onChange={(e) => setForm((prev) => ({ ...prev, department: e.target.value }))}
                  className="mt-1.5 w-full px-3 py-2.5 rounded-xl border border-slate-200 focus:border-sky-400 focus:ring-2 focus:ring-sky-100 outline-none"
                />
              </div>

              <div className="md:col-span-2">
                <label className="text-sm font-medium text-slate-700">Bio</label>
                <textarea
                  rows={4}
                  value={form.bio}
                  onChange={(e) => setForm((prev) => ({ ...prev, bio: e.target.value }))}
                  className="mt-1.5 w-full px-3 py-2.5 rounded-xl border border-slate-200 focus:border-sky-400 focus:ring-2 focus:ring-sky-100 outline-none"
                />
              </div>
            </div>

            <div className="mt-5 flex justify-end">
              <button
                onClick={saveProfile}
                className="inline-flex items-center gap-2 px-4 py-2.5 rounded-xl bg-sky-600 text-white font-semibold hover:bg-sky-700"
              >
                <Save className="w-4 h-4" />
                Save Profile
              </button>
            </div>
          </section>

          <section className="bg-white rounded-2xl premium-shadow p-6">
            <div className="flex items-center gap-2 mb-4">
              <KeyRound className="w-5 h-5 text-indigo-600" />
              <h2 className="text-lg font-bold text-slate-800">Security</h2>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <label className="text-sm font-medium text-slate-700">Current Password</label>
                <input
                  type="password"
                  value={passwordForm.currentPassword}
                  onChange={(e) => setPasswordForm((prev) => ({ ...prev, currentPassword: e.target.value }))}
                  className="mt-1.5 w-full px-3 py-2.5 rounded-xl border border-slate-200 focus:border-indigo-400 focus:ring-2 focus:ring-indigo-100 outline-none"
                />
              </div>

              <div>
                <label className="text-sm font-medium text-slate-700">New Password</label>
                <input
                  type="password"
                  value={passwordForm.newPassword}
                  onChange={(e) => setPasswordForm((prev) => ({ ...prev, newPassword: e.target.value }))}
                  className="mt-1.5 w-full px-3 py-2.5 rounded-xl border border-slate-200 focus:border-indigo-400 focus:ring-2 focus:ring-indigo-100 outline-none"
                />
              </div>

              <div>
                <label className="text-sm font-medium text-slate-700">Confirm Password</label>
                <input
                  type="password"
                  value={passwordForm.confirmPassword}
                  onChange={(e) => setPasswordForm((prev) => ({ ...prev, confirmPassword: e.target.value }))}
                  className="mt-1.5 w-full px-3 py-2.5 rounded-xl border border-slate-200 focus:border-indigo-400 focus:ring-2 focus:ring-indigo-100 outline-none"
                />
              </div>
            </div>

            <div className="mt-5 flex justify-end">
              <button
                onClick={updatePassword}
                className="inline-flex items-center gap-2 px-4 py-2.5 rounded-xl bg-indigo-600 text-white font-semibold hover:bg-indigo-700"
              >
                <KeyRound className="w-4 h-4" />
                Update Password
              </button>
            </div>
          </section>
        </div>
      </div>
    </div>
  )
}
