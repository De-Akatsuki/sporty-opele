const FLAG_MAP = {
  Brazil: '🇧🇷',
  France: '🇫🇷',
  England: '🏴󠁧󠁢󠁥󠁮󠁧󠁿',
  Germany: '🇩🇪',
  Spain: '🇪🇸',
  Argentina: '🇦🇷',
  Portugal: '🇵🇹',
  Netherlands: '🇳🇱',
  Belgium: '🇧🇪',
  Italy: '🇮🇹',
  USA: '🇺🇸',
  'United States': '🇺🇸',
  Mexico: '🇲🇽',
  Japan: '🇯🇵',
  'South Korea': '🇰🇷',
  'Korea Republic': '🇰🇷',
  Morocco: '🇲🇦',
  Senegal: '🇸🇳',
  Australia: '🇦🇺',
  Canada: '🇨🇦',
  Croatia: '🇭🇷',
  Denmark: '🇩🇰',
  Poland: '🇵🇱',
  'Saudi Arabia': '🇸🇦',
  Iran: '🇮🇷',
  Qatar: '🇶🇦',
  Cameroon: '🇨🇲',
  Tunisia: '🇹🇳',
  'Costa Rica': '🇨🇷',
  Wales: '🏴󠁧󠁢󠁷󠁬󠁳󠁿',
  Ecuador: '🇪🇨',
}

export function getFlag(teamName) {
  if (!teamName) return '🏳️'
  return FLAG_MAP[teamName] || '🏳️'
}
