import { Activity } from 'lucide-react'

function Chip({ label, value }) {
  if (value == null || value === '') return null
  return (
    <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-md bg-[#f6f9fc] border border-[#e3e8ef] text-[10px] text-[#546e7a]">
      <span className="text-[#94a3b8]">{label}</span>
      <span className="font-mono text-[#0a2540]">{value}</span>
    </span>
  )
}

export default function FixtureFeatureSummary({ features }) {
  if (!features) return null

  const confidence = features.data_confidence
  const corners = features.total_corners_avg_combined
  const xg = features.combined_xg
  const btts = features.btts_base_prob
  const elo = features.elo_differential

  return (
    <div className="mt-3 pt-3 border-t border-[#e3e8ef]">
      <div className="flex items-center gap-1.5 mb-2">
        <Activity size={12} className="text-[#0570de]" />
        <span className="text-[10px] font-medium uppercase tracking-wide text-[#94a3b8]">
          Engineered features
        </span>
        {confidence && (
          <span
            className={`ml-auto text-[10px] font-medium uppercase ${
              confidence === 'high'
                ? 'text-[#09b572]'
                : confidence === 'medium'
                  ? 'text-[#f59e0b]'
                  : 'text-[#94a3b8]'
            }`}
          >
            {confidence} confidence
          </span>
        )}
      </div>
      <div className="flex flex-wrap gap-1.5">
        <Chip
          label="Corners exp."
          value={corners != null ? Number(corners).toFixed(1) : null}
        />
        <Chip label="Combined xG" value={xg != null ? Number(xg).toFixed(2) : null} />
        <Chip
          label="BTTS base"
          value={btts != null ? `${Math.round(Number(btts) * 100)}%` : null}
        />
        <Chip
          label="Elo Δ"
          value={elo != null ? (elo > 0 ? `+${Math.round(elo)}` : Math.round(elo)) : null}
        />
      </div>
    </div>
  )
}
