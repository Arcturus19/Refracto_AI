import React, { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Menu, Bell, ChevronDown, LogOut, User } from 'lucide-react'
import { useAuthStore } from '../store/useAuthStore'

interface HeaderProps {
    onMenuClick: () => void
}

export default function Header({ onMenuClick }: HeaderProps) {
    const navigate = useNavigate()
    const { user, logout } = useAuthStore()
    const [dropdownOpen, setDropdownOpen] = useState(false)

    const handleLogout = () => {
        logout()
        navigate('/login')
    }

    // Generate initials from user's full name
    const initials = user?.full_name
        ? user.full_name.split(' ').map(n => n[0]).join('').slice(0, 2).toUpperCase()
        : 'RX'

    return (
        <header className="fixed top-0 right-0 left-0 lg:left-64 h-16 bg-white border-b border-slate-200 z-30 px-4 flex items-center justify-between">
            <div className="flex items-center gap-4">
                <button
                    onClick={onMenuClick}
                    className="p-2 -ml-2 hover:bg-slate-100 rounded-md text-slate-500 lg:hidden"
                >
                    <Menu size={24} />
                </button>

                {/* Connection Status */}
                <div className="hidden md:flex items-center gap-2 px-3 py-1.5 bg-emerald-50 text-emerald-700 rounded-full text-xs font-semibold border border-emerald-100">
                    <div className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
                    AI Server Online
                </div>
            </div>

            <div className="flex items-center gap-4">
                <button className="p-2 hover:bg-slate-100 rounded-full text-slate-500 relative">
                    <Bell size={20} />
                    <span className="absolute top-1.5 right-1.5 w-2 h-2 bg-red-500 rounded-full border-2 border-white" />
                </button>

                <div className="h-8 w-px bg-slate-200 mx-1" />

                {/* User Dropdown */}
                <div className="relative">
                    <button
                        onClick={() => setDropdownOpen(!dropdownOpen)}
                        className="flex items-center gap-3 pl-2 pr-1 py-1 hover:bg-slate-50 rounded-full border border-transparent hover:border-slate-200 transition-all"
                    >
                        <div className="w-8 h-8 rounded-full bg-gradient-to-br from-blue-500 to-cyan-400 flex items-center justify-center text-white text-xs font-bold">
                            {initials}
                        </div>
                        <div className="hidden md:block text-left mr-2">
                            <div className="text-sm font-semibold text-slate-700">
                                {user?.full_name || 'Loading...'}
                            </div>
                            <div className="text-xs text-slate-500 capitalize">
                                {user?.role || '—'}
                            </div>
                        </div>
                        <ChevronDown
                            size={16}
                            className={`text-slate-400 mr-2 transition-transform ${dropdownOpen ? 'rotate-180' : ''}`}
                        />
                    </button>

                    {/* Dropdown Menu */}
                    {dropdownOpen && (
                        <div className="absolute right-0 mt-2 w-52 bg-white border border-slate-200 rounded-xl shadow-lg py-1 z-50">
                            <div className="px-4 py-2.5 border-b border-slate-100">
                                <p className="text-sm font-semibold text-slate-800 truncate">{user?.full_name}</p>
                                <p className="text-xs text-slate-400 truncate">{user?.email}</p>
                            </div>

                            <button
                                onClick={() => setDropdownOpen(false)}
                                className="w-full flex items-center gap-2 px-4 py-2.5 text-sm text-slate-600 hover:bg-slate-50 transition-colors"
                            >
                                <User size={15} />
                                My Profile
                            </button>

                            <button
                                onClick={handleLogout}
                                className="w-full flex items-center gap-2 px-4 py-2.5 text-sm text-red-600 hover:bg-red-50 transition-colors"
                            >
                                <LogOut size={15} />
                                Log Out
                            </button>
                        </div>
                    )}
                </div>
            </div>

            {/* Close dropdown on outside click */}
            {dropdownOpen && (
                <div
                    className="fixed inset-0 z-40"
                    onClick={() => setDropdownOpen(false)}
                />
            )}
        </header>
    )
}
