import { useState } from 'react'
import { AlertCircle, LogOut } from 'lucide-react'
import { useAuth } from '../contexts/AuthContext'

export default function LoginPage() {
  const { signIn, signUp, error } = useAuth()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [isSignUp, setIsSignUp] = useState(false)
  const [loading, setLoading] = useState(false)
  const [localError, setLocalError] = useState(null)

  async function handleSubmit(e) {
    e.preventDefault()
    setLoading(true)
    setLocalError(null)

    try {
      if (!email || !password) {
        throw new Error('Email and password are required')
      }

      if (isSignUp) {
        await signUp(email, password)
      } else {
        await signIn(email, password)
      }
    } catch (err) {
      setLocalError(err.message)
    } finally {
      setLoading(false)
    }
  }

  const displayError = localError || error

  return (
    <div className="min-h-screen bg-[#f6f9fc] flex items-center justify-center px-4 relative overflow-hidden">
      {/* Background shapes */}
      <div className="absolute inset-0 pointer-events-none">
        {/* Top right large circle */}
        <div className="absolute top-0 right-0 w-96 h-96 bg-gradient-to-br from-[#eff6ff] to-transparent rounded-full blur-3xl opacity-40 -translate-y-1/3 translate-x-1/3" />

        {/* Bottom left accent */}
        <div className="absolute bottom-0 left-0 w-80 h-80 bg-gradient-to-tr from-[#eff6ff] to-transparent rounded-full blur-3xl opacity-30 translate-y-1/3 -translate-x-1/4" />

        {/* Center subtle grid */}
        <svg className="absolute inset-0 w-full h-full opacity-5" preserveAspectRatio="none">
          <defs>
            <pattern id="grid" width="40" height="40" patternUnits="userSpaceOnUse">
              <path d="M 40 0 L 0 0 0 40" fill="none" stroke="#0a2540" strokeWidth="0.5" />
            </pattern>
          </defs>
          <rect width="100%" height="100%" fill="url(#grid)" />
        </svg>
      </div>

      {/* Card */}
      <div className="relative z-10 w-full max-w-sm">
        {/* Header */}
        <div className="mb-8 text-center">
          <div className="text-3xl mb-2">⚽</div>
          <h1 className="text-2xl font-semibold text-[#0a2540] tracking-tight mb-1">
            Sporty-Opele
          </h1>
          <p className="text-sm text-[#94a3b8]">
            WC 2026 Prediction Analytics
          </p>
        </div>

        {/* Form card */}
        <div className="bg-white border border-[#e3e8ef] rounded-xl p-6 shadow-sm">
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-xs font-medium text-[#546e7a] mb-1.5 uppercase tracking-wide">
                Email
              </label>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="you@example.com"
                className="w-full px-3 py-2 border border-[#e3e8ef] rounded-lg text-sm focus:border-[#0570de] focus:ring-1 focus:ring-[#0570de] outline-none bg-white text-[#0a2540] placeholder:text-[#94a3b8]"
                disabled={loading}
              />
            </div>

            <div>
              <label className="block text-xs font-medium text-[#546e7a] mb-1.5 uppercase tracking-wide">
                Password
              </label>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
                className="w-full px-3 py-2 border border-[#e3e8ef] rounded-lg text-sm focus:border-[#0570de] focus:ring-1 focus:ring-[#0570de] outline-none bg-white text-[#0a2540] placeholder:text-[#94a3b8]"
                disabled={loading}
              />
            </div>

            {displayError && (
              <div className="flex items-center gap-2 px-3 py-2 bg-[#fee2e2] border border-[#fecaca] rounded-lg">
                <AlertCircle size={14} className="text-[#dc2626] shrink-0" />
                <span className="text-xs text-[#991b1b]">{displayError}</span>
              </div>
            )}

            <button
              type="submit"
              disabled={loading}
              className="w-full py-2 px-4 bg-[#0570de] text-white rounded-lg text-sm font-medium hover:bg-[#0560c9] active:bg-[#0450b8] disabled:opacity-50 disabled:cursor-not-allowed transition-colors duration-100 mt-1"
            >
              {loading ? 'Loading...' : isSignUp ? 'Create Account' : 'Sign In'}
            </button>
          </form>

          {/* Toggle */}
          <div className="mt-4 text-center">
            <p className="text-xs text-[#94a3b8]">
              {isSignUp ? 'Already have an account?' : "Don't have an account?"}{' '}
              <button
                type="button"
                onClick={() => {
                  setIsSignUp(!isSignUp)
                  setLocalError(null)
                }}
                className="text-[#0570de] font-medium hover:text-[#0560c9] transition-colors"
              >
                {isSignUp ? 'Sign in' : 'Create one'}
              </button>
            </p>
          </div>
        </div>

        {/* Footer text */}
        <p className="text-center text-[11px] text-[#94a3b8] mt-6">
          This is a demo. Use any email/password to sign up.
        </p>
      </div>
    </div>
  )
}
