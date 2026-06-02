import { useState, useEffect } from 'react'
import { BarChart2, AlertCircle } from 'lucide-react'
import { supabase } from '../lib/supabaseClient'
import {
  MARKET_LABELS,
  formatProbability,
  isPositivePrediction,
  probabilityColor,
} from '../lib/markets'
import FixtureFeatureSummary from './FixtureFeatureSummary'

function predictionBadge(prediction) {
  const isPositive = isPositivePrediction(prediction)
  const label = prediction?.toUpperCase()
  return (
    <span
      className={`inline-flex items-center px-2 py-0.5 rounded-full text-[11px] font-medium tracking-wide ${
        isPositive
          ? 'bg-[#d1fae5] text-[#065f46]'
          : 'bg-[#fee2e2] text-[#991b1b]'
      }`}
    >
      {label}
    </span>
  )
}

function MarketRow({ market, prediction, probability, confidence_tier }) {
  const label = MARKET_LABELS[market] || market
  const pct = formatProbability(probability)

  return (
    <div className="flex items-center gap-3 py-2 border-b border-[#e3e8ef] last:border-0">
      <span className="text-sm text-[#546e7a] w-40 shrink-0">{label}</span>
      <div className="shrink-0">{predictionBadge(prediction)}</div>
      <div className="flex-1 mx-2 min-w-[60px]">
        <div className="h-1 bg-[#e3e8ef] rounded-full overflow-hidden">
          <div
            className="h-full bg-[#0570de] rounded-full transition-all"
            style={{ width: `${Math.round((probability || 0) * 100)}%` }}
          />
        </div>
      </div>
      <span
        className={`text-xs font-mono w-14 text-right shrink-0 ${probabilityColor(probability, confidence_tier)}`}
      >
        {pct}
        {confidence_tier === 'High' && (
          <span className="block text-[9px] text-[#09b572] font-sans">High</span>
        )}
      </span>
    </div>
  )
}

function SkeletonCard() {
  return (
    <div className="bg-white border border-[#e3e8ef] rounded-xl p-5 animate-pulse">
      <div className="flex justify-between mb-4">
        <div className="h-4 w-20 bg-gray-100 rounded" />
        <div className="h-4 w-24 bg-gray-100 rounded" />
      </div>
      <div className="flex justify-center items-center gap-4 mb-5">
        <div className="h-5 w-28 bg-gray-100 rounded" />
        <div className="h-4 w-6 bg-gray-100 rounded" />
        <div className="h-5 w-28 bg-gray-100 rounded" />
      </div>
      <div className="space-y-3">
        {[...Array(5)].map((_, i) => (
          <div key={i} className="flex items-center gap-3">
            <div className="h-3 w-32 bg-gray-100 rounded" />
            <div className="h-4 w-14 bg-gray-100 rounded-full" />
            <div className="flex-1 h-1 bg-gray-100 rounded" />
            <div className="h-3 w-8 bg-gray-100 rounded" />
          </div>
        ))}
      </div>
    </div>
  )
}

function stageBadge(stage, groupName) {
  const text = stage || (groupName ? `Group ${groupName}` : null)
  if (!text) return null
  return (
    <span className="inline-flex items-center px-2 py-0.5 rounded-full text-[11px] font-medium bg-[#eff6ff] text-[#0570de] border border-[#bfdbfe]">
      {text}
    </span>
  )
}

export default function MatchPredictions({ date, includeUpcoming = false }) {
  const [fixtures, setFixtures] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    if (!date && !includeUpcoming) return
    setLoading(true)
    setError(null)

    async function fetchFixtures() {
      try {
        let query = supabase
          .from('wc_fixtures')
          .select(
            `
            *,
            predictions (
              market,
              prediction,
              probability,
              confidence_tier,
              sentiment_signal,
              model_version
            ),
            processed_features (
              data_confidence,
              total_corners_avg_combined,
              combined_xg,
              btts_base_prob,
              elo_differential
            )
          `
          )
          .order('kickoff_time', { ascending: true, nullsFirst: false })

        if (date) {
          query = query.eq('match_date', date)
        } else if (includeUpcoming) {
          query = query.eq('match_completed', false)
        }

        const { data, error: err } = await query
        if (err) throw err

        const rows = (data || []).map((f) => ({
          ...f,
          processed_features: Array.isArray(f.processed_features)
            ? f.processed_features[0]
            : f.processed_features,
        }))

        setFixtures(rows)
      } catch (e) {
        setError(e.message)
      } finally {
        setLoading(false)
      }
    }

    fetchFixtures()
  }, [date, includeUpcoming])

  if (loading) {
    return (
      <div className="space-y-4">
        {[...Array(3)].map((_, i) => (
          <SkeletonCard key={i} />
        ))}
      </div>
    )
  }

  if (error) {
    return (
      <div className="bg-white border border-[#e3e8ef] rounded-xl p-8 flex items-center gap-3 text-[#546e7a]">
        <AlertCircle size={18} className="text-[#df1b41] shrink-0" />
        <span className="text-sm">Failed to load data. Check your Supabase connection.</span>
      </div>
    )
  }

  if (!fixtures.length) {
    return (
      <div className="bg-white border border-[#e3e8ef] rounded-xl p-12 flex flex-col items-center gap-3 text-center">
        <BarChart2 size={32} className="text-[#94a3b8]" />
        <p className="text-sm text-[#546e7a]">No matches scheduled for this view.</p>
        <p className="text-xs text-[#94a3b8]">
          Run the backend pipeline to seed fixtures and generate predictions.
        </p>
      </div>
    )
  }

  return (
    <div className="space-y-4">
      {fixtures.map((fixture) => {
        const preds = fixture.predictions || []
        const features = fixture.processed_features
        const dateLabel = fixture.match_date
          ? new Date(fixture.match_date).toLocaleDateString('en-GB', {
              weekday: 'short',
              day: 'numeric',
              month: 'short',
            })
          : ''
        const kickoff = fixture.kickoff_time
          ? String(fixture.kickoff_time).slice(0, 5)
          : null

        return (
          <div
            key={fixture.id}
            className="bg-white border border-[#e3e8ef] rounded-xl p-5"
          >
            <div className="flex items-center justify-between mb-4">
              {stageBadge(fixture.stage, fixture.group_name)}
              <div className="text-right">
                <span className="text-[12px] text-[#94a3b8] font-mono block">
                  {dateLabel}
                </span>
                {kickoff && (
                  <span className="text-[11px] text-[#94a3b8]">{kickoff}</span>
                )}
              </div>
            </div>

            <div className="flex items-center justify-center gap-4 mb-5">
              <span className="text-[15px] font-semibold text-[#0a2540] tracking-tight">
                {fixture.home_team}
              </span>
              <span className="text-xs text-[#94a3b8] font-medium">vs</span>
              <span className="text-[15px] font-semibold text-[#0a2540] tracking-tight">
                {fixture.away_team}
              </span>
            </div>

            {preds.length > 0 ? (
              <div className="border border-[#e3e8ef] rounded-lg px-4 py-1">
                {preds.map((p) => (
                  <MarketRow
                    key={`${fixture.id}-${p.market}`}
                    market={p.market}
                    prediction={p.prediction}
                    probability={p.probability}
                    confidence_tier={p.confidence_tier}
                  />
                ))}
              </div>
            ) : (
              <div className="border border-[#e3e8ef] rounded-lg px-4 py-4 text-center">
                <span className="text-xs text-[#94a3b8]">
                  No predictions yet — run{' '}
                  <code className="text-[10px] bg-[#f6f9fc] px-1 rounded">
                    python3 backend/pipeline/run_pipeline.py
                  </code>
                </span>
              </div>
            )}

            <FixtureFeatureSummary features={features} />
          </div>
        )
      })}
    </div>
  )
}
