import { useState } from 'react'
import { X, AlertCircle, TrendingUp } from 'lucide-react'
import { supabase } from '../lib/supabaseClient'
import {
  MARKET_LABELS,
  formatProbability,
  isPositivePrediction,
  isHighConfidencePick,
} from '../lib/markets'

function PredictionBadge({ prediction }) {
  const isPositive = isPositivePrediction(prediction)
  return (
    <span
      className={`inline-flex items-center px-2 py-0.5 rounded-full text-[11px] font-medium ${
        isPositive
          ? 'bg-[#d1fae5] text-[#065f46]'
          : 'bg-[#fee2e2] text-[#991b1b]'
      }`}
    >
      {prediction?.toUpperCase()}
    </span>
  )
}

export default function PredictionCheckerModal({ isOpen, onClose }) {
  const [predictions, setPredictions] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [checked, setChecked] = useState(false)

  async function checkPredictions() {
    setLoading(true)
    setError(null)
    setChecked(false)

    try {
      const today = new Date().toISOString().slice(0, 10)

      const { data, error: err } = await supabase
        .from('predictions')
        .select(
          `
          id,
          market,
          prediction,
          probability,
          confidence_tier,
          model_version,
          wc_fixtures!inner (home_team, away_team, match_date)
        `
        )
        .eq('wc_fixtures.match_date', today)
        .order('probability', { ascending: false })

      if (err) throw err
      setPredictions(data || [])
      setChecked(true)
    } catch (e) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }

  if (!isOpen) return null

  const highCount = predictions.filter(isHighConfidencePick).length

  return (
    <>
      <div
        className="fixed inset-0 bg-black/30 backdrop-blur-sm z-40"
        onClick={onClose}
        role="presentation"
      />

      <div className="fixed inset-0 z-50 flex items-center justify-center px-4 sm:px-6 py-6 pointer-events-none">
        <div
          className="bg-white border border-[#e3e8ef] rounded-xl shadow-lg w-full max-w-2xl max-h-[80vh] overflow-y-auto pointer-events-auto"
          onClick={(e) => e.stopPropagation()}
          role="dialog"
          aria-labelledby="prediction-check-title"
        >
          <div className="sticky top-0 bg-white border-b border-[#e3e8ef] px-6 py-4 flex items-center justify-between">
            <div className="flex items-center gap-2">
              <TrendingUp size={18} className="text-[#0570de]" />
              <h2
                id="prediction-check-title"
                className="text-[15px] font-semibold text-[#0a2540] tracking-tight"
              >
                Today's Predictions
              </h2>
            </div>
            <button
              type="button"
              onClick={onClose}
              className="p-1.5 rounded-lg text-[#546e7a] hover:bg-[#f6f9fc] transition-colors"
              aria-label="Close"
            >
              <X size={18} />
            </button>
          </div>

          <div className="px-6 py-4">
            {!checked ? (
              <div className="text-center py-12">
                <TrendingUp size={40} className="text-[#e3e8ef] mx-auto mb-4" />
                <p className="text-sm text-[#546e7a] mb-4">
                  Fetch all five market predictions for today's fixtures.
                </p>
                <button
                  type="button"
                  onClick={checkPredictions}
                  disabled={loading}
                  className="px-4 py-2 bg-[#0570de] text-white rounded-lg text-sm font-medium hover:bg-[#0560c9] disabled:opacity-50"
                >
                  {loading ? 'Loading...' : 'Load Predictions'}
                </button>
              </div>
            ) : error ? (
              <div className="flex items-center gap-3 px-4 py-3 bg-[#fee2e2] border border-[#fecaca] rounded-lg">
                <AlertCircle size={18} className="text-[#dc2626] shrink-0" />
                <span className="text-sm text-[#991b1b]">{error}</span>
              </div>
            ) : predictions.length === 0 ? (
              <div className="text-center py-12">
                <p className="text-sm text-[#94a3b8]">No predictions for today yet.</p>
              </div>
            ) : (
              <div className="space-y-3">
                {predictions.map((pred) => {
                  const fixture = pred.wc_fixtures
                  const matchName = fixture
                    ? `${fixture.home_team} vs ${fixture.away_team}`
                    : 'Unknown'
                  const marketLabel = MARKET_LABELS[pred.market] || pred.market
                  const high = isHighConfidencePick(pred)

                  return (
                    <div
                      key={pred.id}
                      className="border border-[#e3e8ef] rounded-lg p-3.5 hover:border-[#0570de] transition-all"
                    >
                      <div className="flex items-start justify-between gap-3 mb-2">
                        <span className="text-sm font-medium text-[#0a2540]">{matchName}</span>
                        <span className="text-xs font-mono text-[#0570de] font-medium">
                          {formatProbability(pred.probability)}
                          {high && (
                            <span className="block text-[9px] text-[#09b572]">HIGH</span>
                          )}
                        </span>
                      </div>
                      <div className="flex items-center gap-2 flex-wrap">
                        <span className="text-xs text-[#546e7a]">{marketLabel}</span>
                        <PredictionBadge prediction={pred.prediction} />
                        {pred.confidence_tier && (
                          <span className="text-[10px] text-[#94a3b8]">
                            · {pred.confidence_tier}
                          </span>
                        )}
                        {pred.model_version && (
                          <span className="text-[10px] text-[#94a3b8] font-mono">
                            · {pred.model_version}
                          </span>
                        )}
                      </div>
                    </div>
                  )
                })}
              </div>
            )}
          </div>

          <div className="border-t border-[#e3e8ef] px-6 py-3 bg-[#f6f9fc] text-center">
            <p className="text-[11px] text-[#94a3b8]">
              {checked && predictions.length > 0
                ? `${predictions.length} predictions · ${highCount} high confidence`
                : 'Synced from Supabase predictions table'}
            </p>
          </div>
        </div>
      </div>
    </>
  )
}
