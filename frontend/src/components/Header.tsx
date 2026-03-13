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
        <header className="fixed top-0 right-0 left-0 lg:left-64 h-16 glass-panel z-30 px-6 flex items-center justify-between transition-all duration-300">
            <div className="flex items-center gap-4">
                <button
                    onClick={onMenuClick}
                    className="p-2 -ml-2 hover:bg-slate-100/50 rounded-lg text-slate-500 lg:hidden transition-colors"
                >
                    <Menu size={24} />
                </button>

                {/* Connection Status */}
                <div className="hidden md:flex items-center gap-2 px-3 py-1.5 bg-emerald-500/10 text-emerald-700 rounded-full text-xs font-semibold backdrop-blur-sm">
                    <div className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse shadow-[0_0_8px_rgba(16,185,129,0.5)]" />
                    AI Server Online
                </div>
            </div>

            <div className="flex items-center gap-4">
                <button className="p-2 hover:bg-slate-100/50 rounded-full text-slate-500 relative transition-transform duration-200 hover:-translate-y-0.5">
                    <Bell size={20} />
                    <span className="absolute top-1.5 right-1.5 w-2 h-2 bg-rose-500 rounded-full border border-white" />
                </button>

                <div className="h-6 w-px bg-slate-200/50 mx-1" />

                {/* User Dropdown */}
                <div className="relative">
                    <button
                        onClick={() => setDropdownOpen(!dropdownOpen)}
                        className="flex items-center pl-1 pr-2 py-1 hover:bg-slate-50/50 rounded-full border border-transparent hover:border-slate-200/50 transition-all duration-200 group"
                    >
                        <div className="w-8 h-8 rounded-full bg-gradient-to-br from-sky-400 to-blue-600 flex items-center justify-center text-white text-xs font-bold shadow-sm transition-transform duration-200 group-hover:scale-105">
                            {initials}
                        </div>
                        <div className="hidden md:block text-left mx-2">
                            <div className="text-sm font-semibold text-slate-700 leading-tight">
                                {user?.full_name || 'Loading...'}
                            </div>
                            <div className="text-[11px] font-medium text-slate-400 capitalize">
                                {user?.role || '—'}
                            </div>
                        </div>
                        <ChevronDown
                            size={16}
                            className={`text-slate-400 transition-all duration-300 ${dropdownOpen ? 'rotate-180 text-sky-500' : 'group-hover:translate-y-0.5'}`}
                        />
                    </button>

                    {/* Dropdown Menu */}
                    {dropdownOpen && (
                        <div className="absolute right-0 mt-3 w-56 bg-white/95 backdrop-blur-xl border border-white/20 rounded-2xl premium-shadow py-1 z-50 animate-slide-up origin-top-right">
                            <div className="px-5 py-3 border-b border-slate-100/50">
                                <p className="text-sm font-semibold text-slate-800 truncate">{user?.full_name}</p>
                                <p className="text-xs text-slate-400 truncate mt-0.5">{user?.email}</p>
                            </div>

                            <div className="p-1">
                                <button
                                    onClick={() => setDropdownOpen(false)}
                                    className="w-full flex items-center gap-3 px-4 py-2 text-sm font-medium text-slate-600 hover:bg-sky-50 hover:text-sky-600 rounded-xl transition-colors"
                                >
                                    <User size={16} />
                                    My Profile
                                </button>

                                <button
                                    onClick={handleLogout}
                                    className="w-full flex items-center gap-3 px-4 py-2 text-sm font-medium text-rose-600 hover:bg-rose-50 rounded-xl transition-colors mt-1"
                                >
                                    <LogOut size={16} />
                                    Log Out
                                </button>
                            </div>
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
