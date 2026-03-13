import React from 'react'
import { LayoutDashboard, Users, Brain, FileText, Settings, X, Zap } from 'lucide-react'
import { Link, useLocation } from 'react-router-dom'

interface SidebarProps {
    isOpen: boolean
    onClose: () => void
}

const navItems = [
    { icon: LayoutDashboard, label: 'Dashboard', path: '/' },
    { icon: Users, label: 'Patients', path: '/patients' },
    { icon: Brain, label: 'AI Analysis', path: '/analysis' },
    { icon: FileText, label: 'Reports', path: '/reports' },
    { icon: Settings, label: 'Settings', path: '/settings' },
]

export default function Sidebar({ isOpen, onClose }: SidebarProps) {
    const location = useLocation()

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
        fixed top-0 left-0 z-50 h-screen w-64 bg-white border-r border-slate-200 transition-transform duration-300 ease-in-out
        ${isOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'}
      `}>
                <div className="flex flex-col h-full">

                    {/* Logo Area */}
                    <div className="h-16 flex items-center justify-between px-6 border-b border-slate-200">
                        <h1 className="text-xl font-bold text-slate-800 flex items-center gap-2">
                            <div className="w-8 h-8 bg-sky-600 rounded-lg flex items-center justify-center text-white">R</div>
                            Refracto
                        </h1>
                        <button
                            onClick={onClose}
                            className="lg:hidden p-2 hover:bg-slate-100 rounded-md text-slate-500"
                        >
                            <X size={20} />
                        </button>
                    </div>

                    {/* Navigation */}
                    <nav className="flex-1 overflow-y-auto py-6 px-3 space-y-1">
                        {navItems.map((item) => {
                            const isActive = location.pathname === item.path
                            return (
                                <Link
                                    key={item.label}
                                    to={item.path}
                                    onClick={onClose}
                                    className={`
                    flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors
                    ${isActive
                                            ? 'bg-sky-50 text-sky-700'
                                            : 'text-slate-600 hover:bg-slate-50 hover:text-slate-900'}
                  `}
                                >
                                    <item.icon size={20} />
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
