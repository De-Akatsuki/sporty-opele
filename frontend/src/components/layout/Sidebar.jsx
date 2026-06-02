import { useState, useEffect } from 'react'
import { NavLink } from 'react-router-dom'
import { LayoutDashboard, Users, BarChart2, LogOut, TrendingUp } from 'lucide-react'
import { supabase } from '../../lib/supabaseClient'
import { useAuth } from '../../contexts/AuthContext'
import { LogOut } from 'lucide-react'

const navItems = [
  { to: '/', label: 'Dashboard', icon: LayoutDashboard, end: true },
  { to: '/teams', label: 'Teams', icon: Users },
  { to: '/performance', label: 'Performance', icon: BarChart2 },
]

export default function Sidebar({ mobileOpen, onClose, onCheckPredictions }) {
  const { signOut, devMode } = useAuth()
  const [completedCount, setCompletedCount] = useState(null)
  const [totalFixtures, setTotalFixtures] = useState(null)

  useEffect(() => {
    async function fetchCounts() {
      const [completed, total] = await Promise.all([
        supabase
          .from('wc_fixtures')
          .select('id', { count: 'exact', head: true })
          .eq('match_completed', true),
        supabase.from('wc_fixtures').select('id', { count: 'exact', head: true }),
      ])
      setCompletedCount(completed.count ?? 0)
      setTotalFixtures(total.count ?? 0)
    }
    fetchCounts()
  }, [])

  return (
    <>
      {mobileOpen && (
        <div
          className="fixed inset-0 bg-black/20 z-20 md:hidden"
          onClick={onClose}
          role="presentation"
        />
      )}

      <aside
        className={`
          fixed top-0 left-0 h-full w-60 bg-white border-r border-[#e3e8ef] z-30
          flex flex-col transition-transform duration-200
          ${mobileOpen ? 'translate-x-0' : '-translate-x-full'}
          md:translate-x-0
        `}
      >
        <div className="px-5 py-5 border-b border-[#e3e8ef]">
          <div className="flex items-center gap-2">
            <span className="text-xl">⚽</span>
            <span className="font-semibold text-[#0a2540] tracking-tight text-[15px]">
              Sporty-Opele
            </span>
          </div>
          <p className="text-[11px] text-[#94a3b8] mt-1 ml-7">WC 2026 · 5 markets</p>
          {devMode && (
            <p className="text-[10px] text-[#f59e0b] mt-1 ml-7 font-medium">Dev mode (no auth)</p>
          )}
        </div>

        <nav className="flex-1 py-3 px-2">
          {navItems.map(({ to, label, icon: Icon, end }) => (
            <NavLink
              key={to}
              to={to}
              end={end}
              onClick={onClose}
              className={({ isActive }) =>
                `flex items-center gap-3 px-3 py-2 rounded-lg text-sm mb-0.5 transition-colors ${
                  isActive
                    ? 'border-l-2 border-[#0570de] text-[#0570de] bg-[#eff6ff] font-medium pl-[10px]'
                    : 'text-[#546e7a] hover:bg-[#f6f9fc]'
                }`
              }
            >
              <Icon size={16} strokeWidth={1.75} />
              {label}
            </NavLink>
          ))}
        </nav>

        <div className="px-5 py-4 border-t border-[#e3e8ef] space-y-4">
          <button
            type="button"
            onClick={onCheckPredictions}
            className="w-full flex items-center justify-center gap-2 px-3 py-2 bg-[#eff6ff] text-[#0570de] rounded-lg text-xs font-medium hover:bg-[#0570de] hover:text-white transition-colors border border-[#bfdbfe]"
          >
            <TrendingUp size={14} />
            Check Predictions
          </button>

          <div>
            <p className="text-[11px] text-[#94a3b8] uppercase tracking-wide font-medium mb-1">
              Fixtures tracked
            </p>
            <p className="text-[13px] text-[#546e7a] font-mono">
              {completedCount === null ? '—' : completedCount}
              {totalFixtures != null ? ` / ${totalFixtures}` : ''} complete
            </p>
          </div>

          <button
            type="button"
            onClick={signOut}
            className="w-full flex items-center justify-center gap-2 px-3 py-2 text-[#546e7a] rounded-lg text-xs font-medium hover:bg-[#f6f9fc] transition-colors"
          >
            <LogOut size={14} />
            Sign Out
          </button>
        </div>
      </aside>
    </>
  )
}

// import { supabase } from '../../lib/supabaseClient'
// import { LogOut } from 'lucide-react'

// // inside the component
// const handleSignOut = async () => {
//   await supabase.auth.signOut()
// }

// // in the JSX, at the bottom of the sidebar
// <button
//   onClick={handleSignOut}
//   className="flex items-center gap-2 text-sm text-[#546e7a] hover:text-[#df1b41] transition-colors px-3 py-2 w-full"
// >
//   <LogOut size={15} />
//   Sign out
// </button>