import { useState, useEffect } from 'react'
import { Search, AlertCircle } from 'lucide-react'
import { supabase } from '../lib/supabaseClient'
import Topbar from '../components/layout/Topbar'
import TeamCard from '../components/TeamCard'

const CONFEDERATIONS = ['All', 'UEFA', 'CONMEBOL', 'CONCACAF', 'CAF', 'AFC', 'OFC']

export default function Teams({ onMenuClick }) {
  const [teams, setTeams] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [search, setSearch] = useState('')
  const [activeConf, setActiveConf] = useState('All')

  useEffect(() => {
    async function fetchTeams() {
      try {
        const { data, error: err } = await supabase
          .from('wc_teams')
          .select('*')
          .order('fifa_ranking', { ascending: true, nullsFirst: false })

        if (err) throw err
        setTeams(data || [])
      } catch (e) {
        setError(e.message)
      } finally {
        setLoading(false)
      }
    }
    fetchTeams()
  }, [])

  const filtered = teams.filter((t) => {
    const matchesSearch = t.team_name
      ?.toLowerCase()
      .includes(search.toLowerCase())
    const matchesConf =
      activeConf === 'All' || t.confederation === activeConf
    return matchesSearch && matchesConf
  })

  return (
    <div className="flex flex-col min-h-screen">
      <Topbar title="Teams" onMenuClick={onMenuClick} />

      <div className="flex-1 p-6 max-w-[1200px] w-full mx-auto">
        <p className="text-sm text-[#546e7a] mb-4">
          World Cup squad stats from FootyStats — corners, bookings, goals, xG, and sentiment
          signals used by the feature pipeline.
        </p>

        <div className="mb-6 space-y-3">
          <div className="relative max-w-sm">
            <Search
              size={15}
              className="absolute left-3 top-1/2 -translate-y-1/2 text-[#94a3b8]"
            />
            <input
              type="text"
              placeholder="Search teams..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full border border-[#e3e8ef] rounded-lg pl-9 pr-3 py-2 text-sm focus:border-[#0570de] focus:ring-1 focus:ring-[#0570de] outline-none bg-white text-[#0a2540] placeholder:text-[#94a3b8]"
            />
          </div>

          <div className="flex flex-wrap gap-1.5">
            {CONFEDERATIONS.map((conf) => (
              <button
                key={conf}
                type="button"
                onClick={() => setActiveConf(conf)}
                className={`px-3 py-1 rounded-full text-xs font-medium transition-colors ${
                  activeConf === conf
                    ? 'bg-[#0570de] text-white'
                    : 'bg-white border border-[#e3e8ef] text-[#546e7a] hover:border-[#0570de] hover:text-[#0570de]'
                }`}
              >
                {conf === 'All' ? 'All' : conf}
              </button>
            ))}
          </div>
        </div>

        {error ? (
          <div className="bg-white border border-[#e3e8ef] rounded-xl p-5 flex items-center gap-2 text-[#546e7a]">
            <AlertCircle size={16} className="text-[#df1b41] shrink-0" />
            <span className="text-sm">Failed to load data. Check your Supabase connection.</span>
          </div>
        ) : loading ? (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {[...Array(12)].map((_, i) => (
              <div
                key={i}
                className="bg-white border border-[#e3e8ef] rounded-xl p-5 animate-pulse"
              >
                <div className="flex items-center gap-2 mb-4">
                  <div className="h-8 w-8 bg-gray-100 rounded-full" />
                  <div>
                    <div className="h-4 w-24 bg-gray-100 rounded mb-1" />
                    <div className="h-3 w-16 bg-gray-100 rounded" />
                  </div>
                </div>
                <div className="grid grid-cols-4 gap-2 mb-4">
                  {[...Array(4)].map((_, j) => (
                    <div key={j} className="h-14 bg-gray-100 rounded-lg" />
                  ))}
                </div>
                <div className="h-1 bg-gray-100 rounded" />
              </div>
            ))}
          </div>
        ) : filtered.length === 0 ? (
          <div className="bg-white border border-[#e3e8ef] rounded-xl p-12 text-center">
            <p className="text-sm text-[#94a3b8]">
              {search
                ? `No teams found matching "${search}".`
                : 'No teams in database — run the backend scraper first.'}
            </p>
          </div>
        ) : (
          <>
            <p className="text-[12px] text-[#94a3b8] mb-3">
              {filtered.length} team{filtered.length !== 1 ? 's' : ''}
            </p>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
              {filtered.map((team) => (
                <TeamCard key={team.team_name} team={team} />
              ))}
            </div>
          </>
        )}
      </div>
    </div>
  )
}
