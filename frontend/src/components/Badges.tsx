export function HealthBadge({
  health,
  score,
  fit,
}: {
  health?: string | null
  score?: number | null
  fit?: boolean
}) {
  const h = (health || 'UNKNOWN').toUpperCase()
  const color =
    h === 'HEALTHY'
      ? 'bg-ok/15 text-ok border-ok/30'
      : h === 'WARNING'
        ? 'bg-amber/15 text-amber border-amber/30'
        : h === 'CRITICAL'
          ? 'bg-coral/15 text-coral border-coral/30'
          : 'bg-mist text-ink-soft border-mist'

  return (
    <div className={`inline-flex flex-col gap-1 rounded-lg border px-4 py-3 ${color}`}>
      <div className="text-2xl font-display font-semibold">
        {score != null ? `${score}%` : '—'}
      </div>
      <div className="text-xs font-semibold tracking-wide uppercase">{h}</div>
      {fit != null && (
        <div className="text-xs">
          {fit ? '✓ Fit for Analytics' : '✗ Not fit for Analytics'}
        </div>
      )}
    </div>
  )
}

export function SeverityPills({
  severity,
}: {
  severity?: { high: number; medium: number; low: number; total: number } | null
}) {
  if (!severity) return null
  return (
    <div className="flex flex-wrap gap-2 text-xs">
      <span className="rounded-full bg-coral/15 text-coral px-3 py-1">
        High {severity.high}
      </span>
      <span className="rounded-full bg-amber/15 text-amber px-3 py-1">
        Medium {severity.medium}
      </span>
      <span className="rounded-full bg-sea/10 text-sea px-3 py-1">
        Low {severity.low}
      </span>
      <span className="rounded-full bg-mist px-3 py-1">Total {severity.total}</span>
    </div>
  )
}
