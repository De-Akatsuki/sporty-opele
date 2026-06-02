import { getFlag } from './teamFlags'

export { getFlag } from './teamFlags'

export default function TeamCard({ team }) {
  const name = team.team_name
  const flag = getFlag(name)
  const ranking = team.fifa_ranking ?? '—'
  const ppg = team.ppg != null ? Number(team.ppg).toFixed(2) : '—'
  const goals = team.avg_goals != null ? Number(team.avg_goals).toFixed(2) : '—'
  const corners = team.avg_corners != null ? Number(team.avg_corners).toFixed(1) : '—'
  const cards = team.avg_cards != null ? Number(team.avg_cards).toFixed(1) : '—'
  const bttsPct =
    team.btts_pct != null ? Math.round(Number(team.btts_pct)) : null
  const sentiment = team.sentiment_score ?? 0
  const xg = team.xg != null ? Number(team.xg).toFixed(2) : '—'

  return (
    <div className="bg-white border border-[#e3e8ef] rounded-xl p-5 hover:border-[#0570de] hover:shadow-md transition-all duration-150">
      <div className="flex items-start justify-between mb-3">
        <div className="flex items-center gap-2">
          <span className="text-2xl leading-none">{flag}</span>
          <div>
            <h3 className="font-semibold text-[#0a2540] text-[14px] leading-tight tracking-tight">
              {name}
            </h3>
            <p className="text-[11px] font-mono text-[#546e7a] mt-0.5">
              FIFA #{ranking} · PPG {ppg}
            </p>
          </div>
        </div>
        {team.confederation && (
          <span className="inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-medium bg-[#f6f9fc] text-[#546e7a] border border-[#e3e8ef] shrink-0">
            {team.confederation}
          </span>
        )}
      </div>

      <div className="grid grid-cols-4 gap-2 mb-4">
        {[
          { value: goals, label: 'Goals avg' },
          { value: corners, label: 'Corners' },
          { value: cards, label: 'Cards' },
          { value: xg, label: 'xG' },
        ].map(({ value, label }) => (
          <div
            key={label}
            className="text-center border border-[#e3e8ef] rounded-lg py-2 px-1"
          >
            <span className="block text-[16px] font-mono font-semibold text-[#0a2540] leading-none mb-1">
              {value}
            </span>
            <span className="text-[9px] text-[#94a3b8] leading-tight">{label}</span>
          </div>
        ))}
      </div>

      <div className="mb-3">
        <div className="flex items-center justify-between mb-1.5">
          <span className="text-[11px] text-[#546e7a]">BTTS % (season)</span>
          <span className="text-[11px] font-mono text-[#0a2540]">
            {bttsPct !== null ? `${bttsPct}%` : '—'}
          </span>
        </div>
        <div className="h-1 bg-[#e3e8ef] rounded-full overflow-hidden">
          <div
            className="h-full bg-[#0570de] rounded-full"
            style={{ width: `${bttsPct ?? 0}%` }}
          />
        </div>
      </div>

      <div className="flex items-center justify-between text-[10px] text-[#94a3b8]">
        <span>Reddit sentiment</span>
        <span
          className={`font-mono ${
            sentiment > 0.1
              ? 'text-[#09b572]'
              : sentiment < -0.1
                ? 'text-[#df1b41]'
                : 'text-[#546e7a]'
          }`}
        >
          {sentiment > 0 ? '+' : ''}
          {Number(sentiment).toFixed(2)}
        </span>
      </div>
    </div>
  )
}
