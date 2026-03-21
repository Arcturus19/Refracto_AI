import React, { useEffect, useMemo, useState } from 'react'
import { Users, RefreshCw, AlertCircle } from 'lucide-react'
import DataTable from '../components/DataTable'
import { authService, type User } from '../services/api'
import { useAuthStore } from '../store/useAuthStore'

function formatDate(value: string) {
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return value
  return date.toLocaleDateString()
}

export default function UserManagementPage() {
  const { user } = useAuthStore()
  const [users, setUsers] = useState<User[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const loadUsers = async () => {
    setIsLoading(true)
    setError(null)
    try {
      const data = await authService.getAllUsers()
      setUsers(data)
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Failed to load users.')
    } finally {
      setIsLoading(false)
    }
  }

  useEffect(() => {
    if (user?.role !== 'admin') return
    void loadUsers()
  }, [user?.role])

  const columns = useMemo(
    () => [
      { header: 'ID', accessor: 'id', render: (row: User) => <span className="font-mono text-xs">{row.id}</span> },
      { header: 'Name', accessor: 'full_name', render: (row: User) => <span className="font-semibold text-slate-800">{row.full_name}</span> },
      { header: 'Email', accessor: 'email' },
      {
        header: 'Role',
        accessor: 'role',
        render: (row: User) => (
          <span
            className={`px-2 py-1 rounded-full text-xs font-semibold ${
              row.role === 'admin' ? 'bg-violet-50 text-violet-700' : 'bg-slate-50 text-slate-700'
            }`}
          >
            {row.role}
          </span>
        ),
      },
      { header: 'Created', accessor: 'created_at', render: (row: User) => <span className="text-sm">{formatDate(row.created_at)}</span> },
      { header: 'Updated', accessor: 'updated_at', render: (row: User) => <span className="text-sm">{formatDate(row.updated_at)}</span> },
    ],
    []
  )

  if (user?.role !== 'admin') {
    return (
      <div className="bg-white rounded-2xl premium-shadow border border-slate-200 p-8 max-w-3xl mx-auto">
        <h1 className="text-2xl font-bold text-slate-900 tracking-tight flex items-center gap-2">
          <Users className="w-6 h-6 text-slate-500" />
          User Management
        </h1>
        <p className="text-slate-500 mt-2">This page is available to administrators only.</p>
      </div>
    )
  }

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold text-slate-900 tracking-tight flex items-center gap-2">
            <Users className="w-7 h-7 text-sky-600" />
            User Management
          </h1>
          <p className="text-slate-500 mt-1 font-medium">Manage users and roles.</p>
        </div>

        <button
          onClick={loadUsers}
          className="bg-white hover:bg-slate-50 text-slate-700 px-5 py-2.5 rounded-xl flex items-center gap-2 font-medium border border-slate-200 transition-all duration-200 hover:-translate-y-0.5 shadow-sm"
          title="Refresh users"
          disabled={isLoading}
        >
          <RefreshCw size={18} className={isLoading ? 'animate-spin' : ''} />
          Refresh
        </button>
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg flex items-start gap-3">
          <AlertCircle size={20} className="flex-shrink-0 mt-0.5" />
          <div>
            <p className="font-medium">Error Loading Users</p>
            <p className="text-sm mt-1">{error}</p>
          </div>
        </div>
      )}

      {isLoading ? (
        <div className="bg-white rounded-2xl border border-slate-100 shadow-sm p-16 text-center animate-pulse">
          <div className="w-12 h-12 rounded-full border-4 border-slate-100 border-t-sky-500 animate-spin mx-auto mb-4" />
          <p className="text-slate-500 font-medium">Loading users...</p>
        </div>
      ) : (
        <DataTable columns={columns} data={users} />
      )}
    </div>
  )
}
