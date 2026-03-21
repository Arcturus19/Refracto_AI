import React, { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { Eye, EyeOff, Brain, Activity, ShieldCheck, Loader2 } from 'lucide-react'
import { useAuthStore } from '../store/useAuthStore'
import { authService } from '../services/api'
import { Toaster, toast } from 'sonner'

type Tab = 'login' | 'register'

export default function LoginPage() {
    const navigate = useNavigate()
    const { login, isAuthenticated, isLoading } = useAuthStore()

    const [tab, setTab] = useState<Tab>('login')
    const [showPassword, setShowPassword] = useState(false)

    // Login form state
    const [loginEmail, setLoginEmail] = useState('')
    const [loginPassword, setLoginPassword] = useState('')

    // Register form state
    const [regName, setRegName] = useState('')
    const [regEmail, setRegEmail] = useState('')
    const [regPassword, setRegPassword] = useState('')
    const [regLoading, setRegLoading] = useState(false)

    // Redirect if already authenticated
    useEffect(() => {
        if (isAuthenticated) navigate('/')
    }, [isAuthenticated, navigate])

    const handleLogin = async (e: React.FormEvent) => {
        e.preventDefault()
        try {
            await login({ email: loginEmail, password: loginPassword })
            toast.success('Welcome back!')
            navigate('/')
        } catch {
            toast.error('Invalid email or password.')
        }
    }

    const handleRegister = async (e: React.FormEvent) => {
        e.preventDefault()
        if (regPassword.length < 8) {
            toast.error('Password must be at least 8 characters.')
            return
        }
        setRegLoading(true)
        try {
            await authService.register({ email: regEmail, password: regPassword, full_name: regName })
            toast.success('Account created! Please log in.')
            setTab('login')
            setLoginEmail(regEmail)
        } catch (err: any) {
            toast.error(err.response?.data?.detail || 'Registration failed.')
        } finally {
            setRegLoading(false)
        }
    }

    return (
        <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 flex items-center justify-center p-4">
            <Toaster position="top-center" richColors />

            {/* Background decorations */}
            <div className="absolute inset-0 overflow-hidden pointer-events-none">
                <div className="absolute -top-40 -right-40 w-96 h-96 bg-blue-500 opacity-10 rounded-full blur-3xl" />
                <div className="absolute -bottom-40 -left-40 w-96 h-96 bg-cyan-500 opacity-10 rounded-full blur-3xl" />
            </div>

            <div className="relative w-full max-w-md">
                {/* Logo */}
                <div className="text-center mb-8">
                    <div className="inline-flex items-center justify-center w-16 h-16 bg-gradient-to-br from-blue-500 to-cyan-400 rounded-2xl shadow-lg mb-4">
                        <Brain size={32} className="text-white" />
                    </div>
                    <h1 className="text-3xl font-bold text-white tracking-tight">Refracto AI</h1>
                    <p className="text-slate-400 mt-1 text-sm">Medical Imaging Intelligence Platform</p>
                </div>

                {/* Card */}
                <div className="bg-white/5 backdrop-blur-xl border border-white/10 rounded-2xl shadow-2xl overflow-hidden">

                    {/* Tabs */}
                    <div className="flex border-b border-white/10">
                        {(['login', 'register'] as Tab[]).map(t => (
                            <button
                                key={t}
                                onClick={() => setTab(t)}
                                className={`flex-1 py-4 text-sm font-semibold transition-all ${tab === t
                                        ? 'text-white border-b-2 border-blue-400 bg-white/5'
                                        : 'text-slate-400 hover:text-slate-300'
                                    }`}
                            >
                                {t === 'login' ? 'Sign In' : 'Register'}
                            </button>
                        ))}
                    </div>

                    <div className="p-6">
                        {/* ===== LOGIN FORM ===== */}
                        {tab === 'login' && (
                            <form onSubmit={handleLogin} className="space-y-4">
                                <div>
                                    <label className="block text-xs font-medium text-slate-300 mb-1.5">Email</label>
                                    <input
                                        type="email"
                                        required
                                        value={loginEmail}
                                        onChange={e => setLoginEmail(e.target.value)}
                                        placeholder="doctor@hospital.com"
                                        className="w-full px-4 py-3 rounded-xl bg-white/10 border border-white/10 text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-blue-400 focus:border-transparent transition text-sm"
                                    />
                                </div>

                                <div>
                                    <label className="block text-xs font-medium text-slate-300 mb-1.5">Password</label>
                                    <div className="relative">
                                        <input
                                            type={showPassword ? 'text' : 'password'}
                                            required
                                            value={loginPassword}
                                            onChange={e => setLoginPassword(e.target.value)}
                                            placeholder="••••••••"
                                            className="w-full px-4 py-3 pr-12 rounded-xl bg-white/10 border border-white/10 text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-blue-400 focus:border-transparent transition text-sm"
                                        />
                                        <button
                                            type="button"
                                            onClick={() => setShowPassword(!showPassword)}
                                            className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-200 transition"
                                        >
                                            {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
                                        </button>
                                    </div>
                                </div>

                                <button
                                    type="submit"
                                    disabled={isLoading}
                                    className="w-full py-3 bg-gradient-to-r from-blue-500 to-cyan-500 hover:from-blue-600 hover:to-cyan-600 text-white font-semibold rounded-xl transition-all duration-200 flex items-center justify-center gap-2 shadow-lg shadow-blue-500/30 disabled:opacity-60 disabled:cursor-not-allowed"
                                >
                                    {isLoading ? <Loader2 size={18} className="animate-spin" /> : null}
                                    {isLoading ? 'Signing in...' : 'Sign In'}
                                </button>
                            </form>
                        )}

                        {/* ===== REGISTER FORM ===== */}
                        {tab === 'register' && (
                            <form onSubmit={handleRegister} className="space-y-4">
                                <div>
                                    <label className="block text-xs font-medium text-slate-300 mb-1.5">Full Name</label>
                                    <input
                                        type="text"
                                        required
                                        value={regName}
                                        onChange={e => setRegName(e.target.value)}
                                        placeholder="Dr. Jane Doe"
                                        className="w-full px-4 py-3 rounded-xl bg-white/10 border border-white/10 text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-blue-400 focus:border-transparent transition text-sm"
                                    />
                                </div>

                                <div>
                                    <label className="block text-xs font-medium text-slate-300 mb-1.5">Email</label>
                                    <input
                                        type="email"
                                        required
                                        value={regEmail}
                                        onChange={e => setRegEmail(e.target.value)}
                                        placeholder="doctor@hospital.com"
                                        className="w-full px-4 py-3 rounded-xl bg-white/10 border border-white/10 text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-blue-400 focus:border-transparent transition text-sm"
                                    />
                                </div>

                                <div>
                                    <label className="block text-xs font-medium text-slate-300 mb-1.5">Password</label>
                                    <div className="relative">
                                        <input
                                            type={showPassword ? 'text' : 'password'}
                                            required
                                            minLength={8}
                                            value={regPassword}
                                            onChange={e => setRegPassword(e.target.value)}
                                            placeholder="Min. 8 characters"
                                            className="w-full px-4 py-3 pr-12 rounded-xl bg-white/10 border border-white/10 text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-blue-400 focus:border-transparent transition text-sm"
                                        />
                                        <button
                                            type="button"
                                            onClick={() => setShowPassword(!showPassword)}
                                            className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-200 transition"
                                        >
                                            {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
                                        </button>
                                    </div>
                                </div>

                                <button
                                    type="submit"
                                    disabled={regLoading}
                                    className="w-full py-3 bg-gradient-to-r from-blue-500 to-cyan-500 hover:from-blue-600 hover:to-cyan-600 text-white font-semibold rounded-xl transition-all duration-200 flex items-center justify-center gap-2 shadow-lg shadow-blue-500/30 disabled:opacity-60 disabled:cursor-not-allowed"
                                >
                                    {regLoading ? <Loader2 size={18} className="animate-spin" /> : null}
                                    {regLoading ? 'Creating account...' : 'Create Account'}
                                </button>
                            </form>
                        )}
                    </div>

                    {/* Trust badges */}
                    <div className="px-6 pb-6 flex items-center justify-center gap-6">
                        <div className="flex items-center gap-1.5 text-slate-500 text-xs">
                            <ShieldCheck size={13} className="text-emerald-500" />
                            HIPAA Compliant
                        </div>
                        <div className="flex items-center gap-1.5 text-slate-500 text-xs">
                            <Activity size={13} className="text-blue-400" />
                            AI-Powered
                        </div>
                    </div>
                </div>
            </div>
        </div>
    )
}
