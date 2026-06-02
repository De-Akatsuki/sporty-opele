import { useState, useEffect, useCallback } from 'react'
import { AlertCircle, ChevronUp, ChevronDown, Check, X, Minus } from 'lucide-react'
import { supabase } from '../lib/supabaseClient'
import Topbar from '../components/layout/Topbar'
import AccuracyTracker from '../components/AccuracyTracker'
import { MARKET_LABELS, formatProbability, probabilityColor } from '../lib/markets'

const MODELS = [
  { key: 'corners', name: 'Corners O/U 9.5', modelPrefix: 'corners' },
  { key: 'cards', name: 'Bookings O/U 3.5', modelPrefix: 'cards' },
  { key: 'btts', name: 'BTTS', modelPrefix: 'btts' },
  { key: 'handicap', name: 'Asian Handicap', modelPrefix: 'handicap' },
  { key: 'goals', name: 'Goals O/U 2.5', modelPrefix: 'goals' },
]

function MarketBadge({ market }) {
  const label = MARKET_LABELS[market] || market
  return (
    <span className="inline-flex items-center px-2 py-0.5 rounded-full text-[11px] font-medium bg-[#f6f9fc] text-[#546e7a] border border-[#e3e8ef] whitespace-nowrap">
      {label}
    </span>
  )
}

function SortIcon({ column, sortKey, sortDir }) {
  if (sortKey !== column) return <ChevronUp size={12} className="text-[#e3e8ef]" />
  return sortDir === 'asc' ? (
    <ChevronUp size={12} className="text-[#0570de]" />
  ) : (
    <ChevronDown size={12} className="text-[#0570de]" />
  )
}

function CorrectIcon({ correct }) {
  if (correct === true) return <Check size={14} className="text-[#09b572]" />
  if (correct === false) return <X size={14} className="text-[#df1b41]" />
  return <Minus size={14} className="text-[#94a3b8]" />
}

export default function Performance({ onMenuClick }) {
  const [modelRuns, setModelRuns] = useState([])
  const [modelRunsLoading, setModelRunsLoading] = useState(true)
  const [modelRunsError, setModelRunsError] = useState(null)

  const [outcomes, setOutcomes] = useState([])
  const [outcomesLoading, setOutcomesLoading] = useState(true)
  const [outcomesError, setOutcomesError] = useState(null)

  const [sortKey, setSortKey] = useState('logged_at')
  const [sortDir, setSortDir] = useState('desc')

  useEffect(() => {
    async function fetchModelRuns() {
      try {
        const { data, error: err } = await supabase
          .from('model_runs')
          .select('model_name, market, accuracy, log_loss, brier_score, training_samples, run_at')
          .order('run_at', { ascending: false })

        if (err) throw err

        const latestByMarket = {}
        for (const run of data || []) {
          const key = run.market || run.model_name
          if (!latestByMarket[key]) latestByMarket[key] = run
        }
        setModelRuns(Object.values(latestByMarket))
      } catch (e) {
        setModelRunsError(e.message)
      } finally {
        setModelRunsLoading(false)
      }
    }

    async function fetchOutcomes() {
      try {
        const { data, error: err } = await supabase
          .from('prediction_outcomes')
          .select(
            `
            market,
            prediction,
            probability,
            actual_outcome,
            correct,
            logged_at,
            wc_fixtures (home_team, away_team, match_date, stage)
          `
          )
          .order('logged_at', { ascending: false })
          .limit(100)

        if (err) throw err
        setOutcomes(data || [])
      } catch (e) {
        setOutcomesError(e.message)
      } finally {
        setOutcomesLoading(false)
      }
    }

    fetchModelRuns()
    fetchOutcomes()
  }, [])

  const handleSort = useCallback(
    (key) => {
      if (sortKey === key) {
        setSortDir((d) => (d === 'asc' ? 'desc' : 'asc'))
      } else {
        setSortKey(key)
        setSortDir('asc')
      }
    },
    [sortKey]
  )

  const sortedOutcomes = [...outcomes].sort((a, b) => {
    let va
    let vb
    switch (sortKey) {
      case 'match':
        va = `${a.wc_fixtures?.home_team} ${a.wc_fixtures?.away_team}`
        vb = `${b.wc_fixtures?.home_team} ${b.wc_fixtures?.away_team}`
        break
      case 'market':
        va = a.market || ''
        vb = b.market || ''
        break
      case 'probability':
        va = a.probability || 0
        vb = b.probability || 0
        break
      default:
        va = a.logged_at || ''
        vb = b.logged_at || ''
    }
    if (va < vb) return sortDir === 'asc' ? -1 : 1
    if (va > vb) return sortDir === 'asc' ? 1 : -1
    return 0
  })

  function findRun(marketKey) {
    return modelRuns.find(
      (r) =>
        r.market === marketKey ||
        r.model_name?.toLowerCase().includes(marketKey)
    )
  }

  function thClass(key) {
    return `px-4 py-3 text-left text-[11px] font-medium text-[#94a3b8] uppercase tracking-wide cursor-pointer hover:text-[#546e7a] select-none`
  }

  return (
    <div className="flex flex-col min-h-screen">
      <Topbar title="Performance" onMenuClick={onMenuClick} />

      <div className="flex-1 p-6 max-w-[1200px] w-full mx-auto space-y-8">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div>
            <h2 className="text-[13px] font-semibold text-[#0a2540] uppercase tracking-wide mb-4">
              Latest Model Runs
            </h2>

            {modelRunsError ? (
              <div className="bg-white border border-[#e3e8ef] rounded-xl p-4 flex items-center gap-2">
                <AlertCircle size={16} className="text-[#df1b41] shrink-0" />
                <span className="text-sm text-[#546e7a]">Failed to load model runs.</span>
              </div>
            ) : modelRunsLoading ? (
              <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
                {[...Array(5)].map((_, i) => (
                  <div
                    key={i}
                    className="bg-white border border-[#e3e8ef] rounded-xl p-4 animate-pulse"
                  >
                    <div className="h-3 w-24 bg-gray-100 rounded mb-3" />
                    <div className="h-7 w-12 bg-gray-100 rounded" />
                  </div>
                ))}
              </div>
            ) : (
              <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
                {MODELS.map(({ key, name }) => {
                  const run = findRun(key)
                  const accuracy =
                    run?.accuracy != null
                      ? `${Math.round(Number(run.accuracy) * 100)}%`
                      : '—'
                  const brier =
                    run?.brier_score != null
                      ? Number(run.brier_score).toFixed(3)
                      : '—'

                  return (
                    <div
                      key={key}
                      className="bg-white border border-[#e3e8ef] rounded-xl p-4"
                    >
                      <p className="text-[11px] font-medium text-[#0a2540] mb-2 leading-tight">
                        {name}
                      </p>
                      <span className="block text-[26px] font-mono font-semibold text-[#0a2540] leading-none mb-1">
                        {accuracy}
                      </span>
                      <span className="text-[11px] text-[#94a3b8]">
                        Brier: <span className="font-mono">{brier}</span>
                      </span>
                    </div>
                  )
                })}
              </div>
            )}
          </div>

          <div>
            <h2 className="text-[13px] font-semibold text-[#0a2540] uppercase tracking-wide mb-4">
              Live Accuracy Breakdown
            </h2>
            <AccuracyTracker />
          </div>
        </div>

        <div>
          <h2 className="text-[13px] font-semibold text-[#0a2540] uppercase tracking-wide mb-4">
            Outcome Log
          </h2>

          {outcomesError ? (
            <div className="bg-white border border-[#e3e8ef] rounded-xl p-4 flex items-center gap-2">
              <AlertCircle size={16} className="text-[#df1b41] shrink-0" />
              <span className="text-sm text-[#546e7a]">Failed to load outcomes.</span>
            </div>
          ) : outcomesLoading ? (
            <div className="bg-white border border-[#e3e8ef] rounded-xl h-48 animate-pulse" />
          ) : sortedOutcomes.length === 0 ? (
            <div className="bg-white border border-[#e3e8ef] rounded-xl p-10 text-center">
              <p className="text-sm text-[#94a3b8]">
                No outcomes logged yet. Complete a match and run the feedback script.
              </p>
            </div>
          ) : (
            <div className="bg-white border border-[#e3e8ef] rounded-xl overflow-hidden">
              <div className="overflow-x-auto">
                <table className="w-full min-w-[760px]">
                  <thead>
                    <tr className="bg-[#f6f9fc] border-b border-[#e3e8ef]">
                      <th className={thClass('match')} onClick={() => handleSort('match')}>
                        <span className="flex items-center gap-1">
                          Match <SortIcon column="match" sortKey={sortKey} sortDir={sortDir} />
                        </span>
                      </th>
                      <th className={thClass('market')} onClick={() => handleSort('market')}>
                        <span className="flex items-center gap-1">
                          Market <SortIcon column="market" sortKey={sortKey} sortDir={sortDir} />
                        </span>
                      </th>
                      <th className="px-4 py-3 text-left text-[11px] font-medium text-[#94a3b8] uppercase tracking-wide">
                        Predicted
                      </th>
                      <th className="px-4 py-3 text-left text-[11px] font-medium text-[#94a3b8] uppercase tracking-wide">
                        Actual
                      </th>
                      <th
                        className={thClass('probability')}
                        onClick={() => handleSort('probability')}
                      >
                        <span className="flex items-center gap-1">
                          Prob.{' '}
                          <SortIcon
                            column="probability"
                            sortKey={sortKey}
                            sortDir={sortDir}
                          />
                        </span>
                      </th>
                      <th className="px-4 py-3 text-left text-[11px] font-medium text-[#94a3b8] uppercase tracking-wide">
                        OK?
                      </th>
                    </tr>
                  </thead>
                  <tbody>
                    {sortedOutcomes.map((row) => {
                      const fixture = row.wc_fixtures
                      const matchName = fixture
                        ? `${fixture.home_team} vs ${fixture.away_team}`
                        : '—'

                      return (
                        <tr
                          key={`${row.market}-${row.logged_at}-${matchName}`}
                          className="border-b border-[#e3e8ef] hover:bg-[#f6f9fc]"
                        >
                          <td className="px-4 py-3 text-sm text-[#0a2540] font-medium">
                            {matchName}
                          </td>
                          <td className="px-4 py-3">
                            <MarketBadge market={row.market} />
                          </td>
                          <td className="px-4 py-3 text-sm font-mono text-[#546e7a]">
                            {row.prediction?.toUpperCase()}
                          </td>
                          <td className="px-4 py-3 text-sm font-mono text-[#546e7a]">
                            {row.actual_outcome?.toUpperCase()}
                          </td>
                          <td
                            className={`px-4 py-3 text-sm font-mono ${probabilityColor(row.probability)}`}
                          >
                            {formatProbability(row.probability)}
                          </td>
                          <td className="px-4 py-3">
                            <CorrectIcon correct={row.correct} />
                          </td>
                        </tr>
                      )
                    })}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
