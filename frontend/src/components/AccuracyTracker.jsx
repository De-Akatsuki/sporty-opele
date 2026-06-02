import { useState, useEffect } from 'react'
import { AlertCircle } from 'lucide-react'
import { supabase } from '../lib/supabaseClient'
import { MARKET_LABELS } from '../lib/markets'

function accBarColor(accuracyPct) {
  if (accuracyPct >= 65) return 'bg-[#0570de]'
  if (accuracyPct >= 55) return 'bg-[#f59e0b]'
  return 'bg-[#df1b41]'
}

function accTextColor(accuracyPct) {
  if (accuracyPct >= 65) return 'text-[#0a2540]'
  if (accuracyPct >= 55) return 'text-[#f59e0b]'
  return 'text-[#df1b41]'
}

export default function AccuracyTracker() {
  const [stats, setStats] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    async function fetchData() {
      try {
        const { data, error: err } = await supabase.from('market_accuracy').select('*')

        if (err) {
          const fallback = await supabase
            .from('prediction_outcomes')
            .select('market, correct')
          if (fallback.error) throw err

          const byMarket = {}
          for (const row of fallback.data || []) {
            if (!byMarket[row.market]) {
              byMarket[row.market] = { total: 0, correct: 0 }
            }
            byMarket[row.market].total += 1
            if (row.correct) byMarket[row.market].correct += 1
          }

          setStats(
            Object.entries(byMarket).map(([market, { total, correct }]) => ({
              market,
              label: MARKET_LABELS[market] || market,
              total,
              correct,
              accuracy_pct: total > 0 ? (correct / total) * 100 : null,
            }))
          )
          return
        }

        setStats(
          (data || []).map((row) => ({
            market: row.market,
            label: MARKET_LABELS[row.market] || row.market,
            total: row.total_predictions,
            correct: row.correct_predictions,
            accuracy_pct: row.accuracy_pct,
          }))
        )
      } catch (e) {
        setError(e.message)
      } finally {
        setLoading(false)
      }
    }
    fetchData()
  }, [])

  if (loading) {
    return (
      <div className="bg-white border border-[#e3e8ef] rounded-xl p-5 animate-pulse">
        <div className="h-4 w-32 bg-gray-100 rounded mb-4" />
        <div className="space-y-4">
          {[...Array(5)].map((_, i) => (
            <div key={i} className="flex items-center gap-3">
              <div className="h-3 w-32 bg-gray-100 rounded" />
              <div className="h-3 w-10 bg-gray-100 rounded" />
              <div className="flex-1 h-1 bg-gray-100 rounded" />
            </div>
          ))}
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="bg-white border border-[#e3e8ef] rounded-xl p-5 flex items-center gap-2 text-[#546e7a]">
        <AlertCircle size={16} className="text-[#df1b41] shrink-0" />
        <span className="text-xs">Failed to load accuracy data.</span>
      </div>
    )
  }

  const hasData = stats.some((s) => s.total > 0)

  if (!hasData) {
    return (
      <div className="bg-white border border-[#e3e8ef] rounded-xl p-8 text-center">
        <p className="text-sm text-[#94a3b8]">
          No logged outcomes yet. Run{' '}
          <code className="text-[10px] bg-[#f6f9fc] px-1 rounded">
            log_outcomes.py
          </code>{' '}
          after matches complete.
        </p>
      </div>
    )
  }

  return (
    <div className="bg-white border border-[#e3e8ef] rounded-xl overflow-hidden">
      <div className="px-5 py-4 border-b border-[#e3e8ef]">
        <h3 className="text-sm font-semibold text-[#0a2540] tracking-tight">
          Accuracy by Market
        </h3>
        <p className="text-[10px] text-[#94a3b8] mt-0.5">From prediction_outcomes feedback loop</p>
      </div>

      <div className="px-5 py-1">
        {stats.map(({ market, label, total, correct, accuracy_pct }) => {
          const pct =
            accuracy_pct != null ? Math.round(Number(accuracy_pct)) : null

          return (
            <div key={market} className="py-3 border-b border-[#e3e8ef] last:border-0">
              <div className="flex justify-between items-center mb-2">
                <span className="text-sm text-[#0a2540] font-medium">{label}</span>
                <span className={`text-sm font-mono font-medium ${accTextColor(pct)}`}>
                  {pct !== null ? `${pct}%` : '—'}
                </span>
              </div>
              <div className="flex items-center gap-2">
                <div className="flex-1 h-1 bg-[#e3e8ef] rounded-full overflow-hidden">
                  <div
                    className={`h-full rounded-full ${accBarColor(pct)}`}
                    style={{ width: `${pct ?? 0}%` }}
                  />
                </div>
                <span className="text-[11px] text-[#94a3b8]">
                  {correct}/{total}
                </span>
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}
