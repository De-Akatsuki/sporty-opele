import { useState, useEffect } from 'react'
import { AlertCircle } from 'lucide-react'
import { supabase } from '../lib/supabaseClient'
import {
  MARKET_LABELS,
  formatProbability,
  isHighConfidencePick,
  probabilityColor,
} from '../lib/markets'

export default function BetSlip() {
  const [picks, setPicks] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    async function fetchPicks() {
      try {
        const today = new Date().toISOString().slice(0, 10)

        const { data, error: err } = await supabase
          .from('predictions')
          .select(
            `
            market,
            prediction,
            probability,
            confidence_tier,
            wc_fixtures!inner (
              home_team,
              away_team,
              match_date,
              match_completed
            )
          `
          )
          .eq('wc_fixtures.match_date', today)
          .eq('wc_fixtures.match_completed', false)
          .order('probability', { ascending: false })

        if (err) throw err

        const highPicks = (data || []).filter(isHighConfidencePick)
        setPicks(highPicks)
      } catch (e) {
        setError(e.message)
      } finally {
        setLoading(false)
      }
    }
    fetchPicks()
  }, [])

  return (
    <div className="bg-white border border-[#e3e8ef] rounded-xl overflow-hidden">
      <div className="px-5 py-4 border-b border-[#e3e8ef] flex items-center justify-between">
        <div>
          <h3 className="text-sm font-semibold text-[#0a2540] tracking-tight">
            High-Confidence Picks
          </h3>
          <p className="text-[10px] text-[#94a3b8] mt-0.5">
            Tier &quot;High&quot; or probability ≥ 65%
          </p>
        </div>
        {!loading && !error && (
          <span className="inline-flex items-center px-2 py-0.5 rounded-full text-[11px] font-medium bg-[#eff6ff] text-[#0570de] border border-[#bfdbfe]">
            {picks.length}
          </span>
        )}
      </div>

      <div className="divide-y divide-[#e3e8ef]">
        {loading ? (
          <div className="animate-pulse p-5 space-y-4">
            {[...Array(4)].map((_, i) => (
              <div key={i} className="space-y-2">
                <div className="flex justify-between">
                  <div className="h-3.5 w-32 bg-gray-100 rounded" />
                  <div className="h-3.5 w-10 bg-gray-100 rounded" />
                </div>
                <div className="h-3 w-40 bg-gray-100 rounded" />
                <div className="h-1 w-full bg-gray-100 rounded" />
              </div>
            ))}
          </div>
        ) : error ? (
          <div className="p-5 flex items-center gap-2 text-[#546e7a]">
            <AlertCircle size={16} className="text-[#df1b41] shrink-0" />
            <span className="text-xs">Failed to load data. Check your Supabase connection.</span>
          </div>
        ) : picks.length === 0 ? (
          <div className="px-5 py-8 text-center">
            <p className="text-sm text-[#94a3b8]">No high-confidence picks today.</p>
          </div>
        ) : (
          picks.map((pick) => {
            const fixture = pick.wc_fixtures
            const matchName = fixture
              ? `${fixture.home_team} vs ${fixture.away_team}`
              : 'Unknown Match'
            const marketLabel = MARKET_LABELS[pick.market] || pick.market
            const pct = formatProbability(pick.probability)

            return (
              <div key={`${matchName}-${pick.market}`} className="px-5 py-3.5">
                <div className="flex items-start justify-between gap-3 mb-1.5">
                  <span className="text-sm font-medium text-[#0a2540] leading-tight">
                    {matchName}
                  </span>
                  <span
                    className={`text-xs font-mono font-medium shrink-0 ${probabilityColor(
                      pick.probability,
                      pick.confidence_tier
                    )}`}
                  >
                    {pct}
                  </span>
                </div>
                <p className="text-xs text-[#546e7a] mb-2">
                  {marketLabel} · {pick.prediction?.toUpperCase()}
                  {pick.confidence_tier && (
                    <span className="text-[#94a3b8]"> · {pick.confidence_tier}</span>
                  )}
                </p>
                <div className="h-1 bg-[#e3e8ef] rounded-full overflow-hidden">
                  <div
                    className="h-full bg-[#0570de] rounded-full"
                    style={{ width: `${Math.round((pick.probability || 0) * 100)}%` }}
                  />
                </div>
              </div>
            )
          })
        )}
      </div>

      <div className="px-5 py-3 border-t border-[#e3e8ef] bg-[#f6f9fc]">
        <p className="text-[11px] text-[#94a3b8] leading-relaxed">
          Probabilities are calibrated model outputs, not guarantees. For research only.
        </p>
      </div>
    </div>
  )
}
