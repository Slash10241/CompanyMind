interface Props { score: number }

export function ConfidenceBadge({ score }: Props) {
  const pct = Math.round(score * 100)
  const color =
    score >= 0.8 ? 'bg-emerald-50 text-emerald-700 border-emerald-200' :
    score >= 0.5 ? 'bg-amber-50 text-amber-700 border-amber-200' :
                   'bg-red-50 text-red-700 border-red-200'
  const label = score >= 0.8 ? 'High' : score >= 0.5 ? 'Medium' : 'Low'

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
