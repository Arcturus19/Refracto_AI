import React from 'react'

interface ErrorBoundaryProps {
  children: React.ReactNode
}

interface ErrorBoundaryState {
  hasError: boolean
}

export default class ErrorBoundary extends React.Component<ErrorBoundaryProps, ErrorBoundaryState> {
  state: ErrorBoundaryState = { hasError: false }

  static getDerivedStateFromError(): ErrorBoundaryState {
    return { hasError: true }
  }

  componentDidCatch(error: Error) {
    console.error('Unhandled application error:', error)
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="min-h-screen bg-slate-950 text-white flex items-center justify-center p-6">
          <div className="max-w-md w-full rounded-3xl border border-white/10 bg-white/5 backdrop-blur-xl p-8 text-center">
            <p className="text-xs uppercase tracking-[0.3em] text-cyan-300 mb-3">System Recovery</p>
            <h1 className="text-2xl font-semibold mb-3">The interface hit an unexpected error.</h1>
            <p className="text-slate-300 text-sm mb-6">
              Reload the page to restore the session. If the issue persists, inspect the browser console and service logs.
            </p>
            <button
              type="button"
              onClick={() => window.location.reload()}
              className="inline-flex items-center justify-center rounded-xl bg-cyan-400 px-4 py-2 text-slate-950 font-semibold hover:bg-cyan-300 transition-colors"
            >
              Reload Application
            </button>
          </div>
        </div>
      )
    }

    return this.props.children
  }
}