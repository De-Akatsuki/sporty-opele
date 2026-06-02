import { useEffect, useState } from 'react'
import { supabase } from '../lib/supabaseClient'
import Login from '../pages/Login'

export default function AuthGuard({ children }) {
  const [session, setSession] = useState(undefined)

  useEffect(() => {
    supabase.auth.getSession().then(({ data: { session } }) => {
      setSession(session)
    })

    const { data: { subscription } } = supabase.auth.onAuthStateChange((_event, session) => {
      setSession(session)
    })

    return () => subscription.unsubscribe()
  }, [])

  if (session === undefined) {
    return (
      <div className="min-h-screen bg-[#f6f9fc] flex items-center justify-center">
        <div className="w-5 h-5 border-2 border-[#0570de] border-t-transparent rounded-full animate-spin" />
      </div>
    )
  }

  if (!session) return <Login />

  return children
}