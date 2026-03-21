import React, { useMemo } from 'react'
import { LayoutDashboard, Users, Brain, FileText, Settings, X, User, Inbox, ClipboardList, ServerCog } from 'lucide-react'
import { Link, useLocation } from 'react-router-dom'
import { useAuthStore } from '../store/useAuthStore'

interface SidebarProps {
    isOpen: boolean
    onClose: () => void
}

const baseNavItems = [
    { icon: LayoutDashboard, label: 'Dashboard', path: '/' },
    { icon: Inbox, label: 'Scans', path: '/scans' },
    { icon: Users, label: 'Patients', path: '/patients' },
    { icon: Brain, label: 'AI Analysis', path: '/analysis' },
    { icon: FileText, label: 'Reports', path: '/reports' },
    { icon: User, label: 'Profile', path: '/profile' },
    { icon: Settings, label: 'Settings', path: '/settings' },
] as const

const adminNavItems = [
    { icon: ClipboardList, label: 'Audit', path: '/audit' },
    { icon: ServerCog, label: 'System', path: '/system' },
    { icon: Users, label: 'Users', path: '/admin/users' },
] as const

export default function Sidebar({ isOpen, onClose }: SidebarProps) {
    const location = useLocation()
    const { user } = useAuthStore()

    const navItems = useMemo(() => {
        if (user?.role === 'admin') return [...baseNavItems, ...adminNavItems]
        return [...baseNavItems]
    }, [user?.role])

    return (
        <>
            {/* Mobile Overlay */}
            {isOpen && (
                <div
                    className="fixed inset-0 bg-black/50 z-40 lg:hidden"
                    onClick={onClose}
                />
            )}

            {/* Sidebar Container */}
            <aside className={`
        fixed top-0 left-0 z-50 h-screen w-64 bg-white/95 backdrop-blur-md premium-shadow transition-transform duration-300 ease-in-out
        ${isOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'}
      `}>
                <div className="flex flex-col h-full">

                    {/* Logo Area */}
                    <div className="h-16 flex items-center justify-between px-6 border-b border-white/20">
                        <h1 className="text-xl font-bold text-slate-800 flex items-center gap-2">
                            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-sky-400 to-blue-600 flex items-center justify-center text-white shadow-sm">R</div>
                            <span className="tracking-tight">Refracto</span>
                        </h1>
                        <button
                            onClick={onClose}
                            className="lg:hidden p-2 hover:bg-slate-100 rounded-md text-slate-500 transition-colors"
                        >
                            <X size={20} />
                        </button>
                    </div>

                    {/* Navigation */}
                    <nav className="flex-1 overflow-y-auto py-6 px-4 space-y-1.5">
                        {navItems.map((item) => {
                            const isActive = location.pathname === item.path || (item.path !== '/' && location.pathname.startsWith(item.path))
                            return (
                                <Link
                                    key={item.label}
                                    to={item.path}
                                    onClick={onClose}
                                    className={`
                    flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition-all duration-200 group hover:-translate-y-0.5
                    ${isActive
                                            ? 'bg-sky-50 text-sky-700 shadow-sm'
                                            : 'text-slate-500 hover:bg-slate-50 hover:text-slate-900'}
                  `}
                                >
                                    <item.icon 
                                        size={20} 
                                        className={`transition-colors duration-200 ${isActive ? 'text-sky-600' : 'text-slate-400 group-hover:text-sky-500'}`} 
                                    />
                                    {item.label}
                                </Link>
                            )
                        })}
                    </nav>

                    {/* User Profile Summary (Optional Footer) */}
                    <div className="p-4 border-t border-slate-200">
                        {/* Additional content can go here */}
                    </div>
                </div>
            </aside>
        </>
    )
}
