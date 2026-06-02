/** Shared market definitions — aligned with backend models and feature_eng.md */

export const MARKETS = ['corners', 'cards', 'btts', 'handicap', 'goals']

export const MARKET_LABELS = {
  corners: 'Corners O/U 9.5',
  cards: 'Bookings O/U 3.5',
  btts: 'Both Teams To Score',
  handicap: 'Asian Handicap (-0.5)',
  goals: 'Goals O/U 2.5',
}

export const LABEL_KEY_MAP = {
  corners: 'label_corners_over',
  cards: 'label_bookings_over',
  btts: 'label_btts',
  handicap: 'label_handicap_cover',
  goals: 'label_goals_over25',
}

const POSITIVE_PREDICTIONS = new Set(['over', 'yes', 'cover'])

export function isPositivePrediction(prediction) {
  return POSITIVE_PREDICTIONS.has(prediction?.toLowerCase())
}

export function predictionMatchesLabel(prediction, labelValue) {
  if (labelValue == null) return null
  const predictedPositive = isPositivePrediction(prediction)
  return predictedPositive === Boolean(Number(labelValue))
}

export function formatProbability(probability) {
  if (probability == null || Number.isNaN(probability)) return '—'
  return `${Math.round(Number(probability) * 100)}%`
}

export function tierColor(tier) {
  if (tier === 'High') return 'text-[#09b572]'
  if (tier === 'Medium') return 'text-[#f59e0b]'
  return 'text-[#94a3b8]'
}

export function probabilityColor(probability, tier) {
  if (tier === 'High' || probability >= 0.65) return 'text-[#09b572]'
  if (tier === 'Medium' || probability >= 0.55) return 'text-[#0570de]'
  return 'text-[#94a3b8]'
}

export function isHighConfidencePick({ probability, confidence_tier }) {
  if (confidence_tier === 'High') return true
  return Number(probability) >= 0.65
}
