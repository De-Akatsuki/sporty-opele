import { useState } from 'react'
import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { AuthProvider, useAuth } from './contexts/AuthContext'
import { isSupabaseConfigured } from './lib/supabaseClient'
import Sidebar from './components/layout/Sidebar'
import Dashboard from './pages/Dashboard'
import Teams from './pages/Teams'
import Performance from './pages/Performance'
import Login from './pages/Login'
import PredictionCheckerModal from './components/PredictionCheckerModal'

function ProtectedLayout() {
  const [mobileOpen, setMobileOpen] = useState(false)
  const [checkerOpen, setCheckerOpen] = useState(false)

  return (
    <>
      <div className="flex h-screen bg-[#f6f9fc] overflow-hidden relative">
        {/* Background shapes */}
        <div className="fixed inset-0 pointer-events-none overflow-hidden">
          <div className="absolute top-0 right-0 w-[500px] h-[500px] bg-gradient-to-br from-[#eff6ff] to-transparent rounded-full blur-3xl opacity-30 -translate-y-1/3 translate-x-1/4" />
          <div className="absolute bottom-0 left-0 w-[600px] h-[600px] bg-gradient-to-tr from-[#eff6ff] to-transparent rounded-full blur-3xl opacity-20 translate-y-1/4 -translate-x-1/3" />
          <div className="absolute top-1/3 right-1/4 w-72 h-72 bg-gradient-to-br from-[#bfdbfe] to-transparent rounded-full blur-2xl opacity-10 mix-blend-multiply" />
        </div>

        <Sidebar
          mobileOpen={mobileOpen}
          onClose={() => setMobileOpen(false)}
          onCheckPredictions={() => setCheckerOpen(true)}
        />

        <div className="flex-1 md:ml-60 flex flex-col overflow-y-auto relative z-10">
          {!isSupabaseConfigured && (
            <div className="bg-[#fffbeb] border-b border-[#fde68a] px-4 py-2 text-center text-xs text-[#92400e]">
              Supabase not configured — set VITE_SUPABASE_URL and VITE_SUPABASE_ANON_KEY in
              frontend/.env.local
            </div>
          )}
          <Routes>
            <Route
              path="/"
              element={<Dashboard onMenuClick={() => setMobileOpen(true)} />}
            />
            <Route
              path="/teams"
              element={<Teams onMenuClick={() => setMobileOpen(true)} />}
            />
            <Route
              path="/performance"
              element={<Performance onMenuClick={() => setMobileOpen(true)} />}
            />
          </Routes>
        </div>
      </div>

      <PredictionCheckerModal
        isOpen={checkerOpen}
        onClose={() => setCheckerOpen(false)}
      />
    </>
  )
}

function AppContent() {
  const { user, loading } = useAuth()

  if (loading) {
    return (
      <div className="min-h-screen bg-[#f6f9fc] flex items-center justify-center">
        <div className="text-center">
          <div className="text-3xl mb-4">⚽</div>
          <p className="text-sm text-[#94a3b8]">Loading...</p>
        </div>
      </div>
    )
  }

  return user ? <ProtectedLayout /> : <Login />
}

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <AppContent />
      </AuthProvider>
    </BrowserRouter>
  )
}
