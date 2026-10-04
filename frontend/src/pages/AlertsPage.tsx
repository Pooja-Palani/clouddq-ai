import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { useAuth } from '../auth/AuthContext'
import { listAlerts } from '../lib/api'
import type { Alert } from '../types'

export function AlertsPage() {
  const { user } = useAuth()
  const [alerts, setAlerts] = useState<Alert[]>([])
  const [error, setError] = useState('')

  useEffect(() => {
    listAlerts()
      .then(setAlerts)
      .catch((e) => setError(e instanceof Error ? e.message : 'Failed'))
  }, [])

  return (
    <div className="space-y-6">
      <div>
        <h1 className="font-display text-3xl">
          {user?.role === 'DataUser' ? 'Alert inbox' : 'Sent alerts'}
        </h1>
        <p className="text-ink-soft text-sm mt-1">
          Lightweight Business → Data User collaboration (not a full ticketing system).
        </p>
      </div>
      {error && <p className="text-coral text-sm">{error}</p>}
      <div className="space-y-3">
        {alerts.map((a) => (
          <div key={a.alertId} className="rounded-xl border border-mist bg-white/80 p-4">
            <div className="flex flex-wrap justify-between gap-2">
              <div>
                <div className="font-medium">{a.datasetName || a.datasetId}</div>
                <div className="text-xs text-ink-soft">
                  {a.status} · Score {a.dqScore ?? '—'}% · {a.health}
                </div>
              </div>
              <Link to={`/app/datasets/${a.datasetId}`} className="text-sea text-sm font-medium hover:underline">
                Open dataset
              </Link>
            </div>
            <p className="text-sm mt-2">{a.note}</p>
            <p className="text-xs text-ink-soft mt-1">
              From {a.fromEmail || 'business'} · {a.createdAt}
            </p>
            {a.history && (
              <details className="mt-2 text-xs text-ink-soft">
                <summary>Status history</summary>
                <ul className="mt-1 pl-2 space-y-1">
                  {a.history.map((h, i) => (
                    <li key={i}>
                      {h.status} — {h.note} ({h.at})
                    </li>
                  ))}
                </ul>
              </details>
            )}
          </div>
        ))}
        {alerts.length === 0 && (
          <p className="text-ink-soft text-sm">No alerts yet.</p>
        )}
      </div>
    </div>
  )
}
