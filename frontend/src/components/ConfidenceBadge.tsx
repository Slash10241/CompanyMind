interface Props {
  score: number
}

export function ConfidenceBadge({ score }: Props) {
  const pct = Math.round(score * 100)
  const color =
    score >= 0.8 ? 'bg-emerald-500/20 text-emerald-300 border-emerald-500/30' :
    score >= 0.5 ? 'bg-amber-500/20 text-amber-300 border-amber-500/30' :
                   'bg-red-500/20 text-red-300 border-red-500/30'
  const label =
    score >= 0.8 ? 'High' : score >= 0.5 ? 'Medium' : 'Low'

  return (
    <span
      className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium border ${color}`}
      title={`Confidence: ${pct}% — based on retrieval score and source diversity`}
    >
      <span className="w-1.5 h-1.5 rounded-full bg-current" />
      {label} confidence ({pct}%)
    </span>
  )
}
