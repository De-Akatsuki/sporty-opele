import { createContext, useContext, useEffect, useState } from 'react'
import { supabase, isSupabaseConfigured } from '../lib/supabaseClient'

const AuthContext = createContext(null)

const DEV_USER = { id: 'dev', email: 'dev@sporty-opele.local' }

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const devMode = !isSupabaseConfigured

  useEffect(() => {
    if (devMode) {
      setUser(DEV_USER)
      setLoading(false)
      return undefined
    }

    let mounted = true

    async function getSession() {
      try {
        const {
          data: { session },
          error: err,
        } = await supabase.auth.getSession()
        if (err) throw err
        if (mounted) setUser(session?.user || null)
      } catch (e) {
        if (mounted) setError(e.message)
      } finally {
        if (mounted) setLoading(false)
      }
    }

    getSession()

    const {
      data: { subscription },
    } = supabase.auth.onAuthStateChange((_event, session) => {
      if (mounted) {
        setUser(session?.user || null)
        setError(null)
      }
    })

    return () => {
      mounted = false
      subscription?.unsubscribe()
    }
  }, [devMode])

  async function signUp(email, password) {
    if (devMode) {
      setUser({ ...DEV_USER, email })
      return { user: DEV_USER }
    }
    setError(null)
    const { data, error: err } = await supabase.auth.signUp({
      email,
      password,
      options: { emailRedirectTo: window.location.origin },
    })
    if (err) {
      setError(err.message)
      throw err
    }
    return data
  }

  async function signIn(email, password) {
    if (devMode) {
      setUser({ ...DEV_USER, email })
      return { user: DEV_USER }
    }
    setError(null)
    const { data, error: err } = await supabase.auth.signInWithPassword({
      email,
      password,
    })
    if (err) {
      setError(err.message)
      throw err
    }
    return data
  }

  async function signOut() {
    if (devMode) {
      setUser(null)
      return
    }
    setError(null)
    const { error: err } = await supabase.auth.signOut()
    if (err) {
      setError(err.message)
      throw err
    }
  }

  return (
    <AuthContext.Provider
      value={{ user, loading, error, signUp, signIn, signOut, devMode }}
    >
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider')
  }
  return context
}
