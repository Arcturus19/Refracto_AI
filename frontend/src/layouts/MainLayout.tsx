import React, { useState } from 'react'
import Sidebar from '../components/Sidebar'
import Header from '../components/Header'

export default function MainLayout({ children }: { children: React.ReactNode }) {
  const [isSidebarOpen, setIsSidebarOpen] = useState(false)

  return (
    <div className="min-h-screen bg-slate-50">
      <Sidebar
        isOpen={isSidebarOpen}
        onClose={() => setIsSidebarOpen(false)}
      />

      <Header
        onMenuClick={() => setIsSidebarOpen(true)}
      />

      {/* Main Content Area */}
      <main className="lg:pl-64 pt-16 min-h-screen transition-all duration-300">
        <div className="p-6 max-w-7xl mx-auto">
          {children}
        </div>
      </main>
    </div>
  )
}
