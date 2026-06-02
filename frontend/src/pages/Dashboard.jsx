import { useState, useEffect } from 'react'
import { AlertCircle } from 'lucide-react'
import { supabase } from '../lib/supabaseClient'
import Topbar from '../components/layout/Topbar'
import MatchPredictions from '../components/MatchPredictions'
import BetSlip from '../components/BetSlip'

function StatCard({ value, label, loading }) {
  if (loading) {
    return (
      <div className="bg-white border border-[#e3e8ef] rounded-xl p-5 animate-pulse">
        <div className="h-8 w-16 bg-gray-100 rounded mb-2" />
        <div className="h-3 w-28 bg-gray-100 rounded" />
      </div>
    )
  }

  return (
    <div className="bg-white border border-[#e3e8ef] rounded-xl p-5">
      <span className="block text-[32px] font-mono font-semibold text-[#0a2540] leading-none mb-1.5">
        {value}
      </span>
      <span className="text-[13px] text-[#94a3b8]">{label}</span>
    </div>
  )
}

export default function Dashboard({ onMenuClick }) {
  const today = new Date().toISOString().slice(0, 10)
  const [stats, setStats] = useState({
    matches: 0,
    predictions: 0,
    highConf: 0,
    features: 0,
  })
  const [statsLoading, setStatsLoading] = useState(true)
  const [statsError, setStatsError] = useState(null)

  useEffect(() => {
    async function fetchStats() {
      try {
        const [fixturesRes, predsRes, featuresRes] = await Promise.all([
          supabase
            .from('wc_fixtures')
            .select('id', { count: 'exact', head: true })
            .eq('match_date', today)
            .eq('match_completed', false),
          supabase
            .from('predictions')
            .select('id, probability, confidence_tier, wc_fixtures!inner(match_date)', {
              count: 'exact',
            })
            .eq('wc_fixtures.match_date', today),
          supabase
            .from('processed_features')
            .select('id, match_date', { count: 'exact' })
            .eq('match_date', today),
        ])

        if (fixturesRes.error) throw fixturesRes.error
        if (predsRes.error) throw predsRes.error

        const preds = predsRes.data || []
        const highConf = preds.filter(
          (p) =>
            p.confidence_tier === 'High' || Number(p.probability) >= 0.65
        ).length

        const featuresToday = (featuresRes.data || []).length

        setStats({
          matches: fixturesRes.count ?? 0,
          predictions: predsRes.count ?? preds.length,
          highConf,
          features: featuresRes.count ?? featuresToday,
        })
      } catch (e) {
        setStatsError(e.message)
      } finally {
        setStatsLoading(false)
      }
    }
    fetchStats()
  }, [today])

  return (
    <div className="flex flex-col min-h-screen">
      <Topbar title="Dashboard" onMenuClick={onMenuClick} />

      <div className="flex-1 p-6 max-w-[1200px] w-full mx-auto">
        {statsError ? (
          <div className="bg-white border border-[#e3e8ef] rounded-xl p-4 mb-6 flex items-center gap-2 text-[#546e7a]">
            <AlertCircle size={16} className="text-[#df1b41] shrink-0" />
            <span className="text-sm">Failed to load data. Check your Supabase connection.</span>
          </div>
        ) : (
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mb-8">
            <StatCard value={stats.matches} label="Today's Matches" loading={statsLoading} />
            <StatCard
              value={stats.predictions}
              label="Model Predictions"
              loading={statsLoading}
            />
            <StatCard
              value={stats.highConf}
              label="High Confidence"
              loading={statsLoading}
            />
            <StatCard
              value={stats.features}
              label="Feature Rows Ready"
              loading={statsLoading}
            />
          </div>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-[1fr_320px] gap-6">
          <div>
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-[13px] font-semibold text-[#0a2540] uppercase tracking-wide">
                Today's Matches
              </h2>
            </div>
            <MatchPredictions date={today} />
          </div>

          <div>
            <div className="mb-4">
              <h2 className="text-[13px] font-semibold text-[#0a2540] uppercase tracking-wide">
                Bet Slip
              </h2>
            </div>
            <BetSlip />
          </div>
        </div>
      </div>
    </div>
  )
}
