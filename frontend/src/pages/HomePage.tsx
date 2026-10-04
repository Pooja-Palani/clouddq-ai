import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { useAuth } from '../auth/AuthContext'
import { listAlerts, listDatasets } from '../lib/api'
import type { Alert, Dataset } from '../types'
import { HealthBadge } from '../components/Badges'

export function HomePage() {
  const { user } = useAuth()
  const [datasets, setDatasets] = useState<Dataset[]>([])
  const [alerts, setAlerts] = useState<Alert[]>([])

  useEffect(() => {
    listDatasets().then(setDatasets).catch(() => setDatasets([]))
    listAlerts().then(setAlerts).catch(() => setAlerts([]))
  }, [])

  const isData = user?.role === 'DataUser'
  const scored = datasets.filter((d) => d.latestScore != null)
  const avg =
    scored.length > 0
      ? Math.round(scored.reduce((s, d) => s + (d.latestScore || 0), 0) / scored.length)
      : null
  const critical = scored.filter((d) => d.latestHealth === 'CRITICAL').length
  const openAlerts = alerts.filter((a) => a.status === 'OPEN').length

  return (
    <div className="space-y-8">
      <div>
        <h1 className="font-display text-3xl">
          {isData ? 'Data User workspace' : 'Business executive view'}
        </h1>
        <p className="text-ink-soft mt-1">
          {isData
            ? 'Upload CSV datasets, run DQ analysis, and resolve quality alerts.'
            : 'Monitor fit-for-use status, read AI summaries, and alert Data Users when quality drops.'}
        </p>
      </div>

      <div className="grid sm:grid-cols-3 gap-4">
        <Kpi label="Datasets" value={String(datasets.length)} />
        <Kpi label="Avg DQ score" value={avg != null ? `${avg}%` : '—'} />
        <Kpi
          label={isData ? 'Open alerts' : 'Critical sets'}
          value={String(isData ? openAlerts : critical)}
        />
      </div>

      <div className="flex flex-wrap gap-3">
        {isData && (
          <Link to="/app/upload" className="rounded-md bg-sea text-white px-4 py-2 text-sm font-medium">
            Upload CSV
          </Link>
        )}
        <Link to="/app/datasets" className="rounded-md border border-mist px-4 py-2 text-sm font-medium hover:bg-mist">
          Browse repository
        </Link>
        <Link to="/app/alerts" className="rounded-md border border-mist px-4 py-2 text-sm font-medium hover:bg-mist">
          Alerts
        </Link>
      </div>

      <section>
        <h2 className="font-display text-xl mb-4">Recent datasets</h2>
        <div className="grid gap-3">
          {datasets.slice(0, 5).map((d) => (
            <Link
              key={d.datasetId}
              to={`/app/datasets/${d.datasetId}`}
              className="flex items-center justify-between gap-4 rounded-xl border border-mist bg-white/80 px-4 py-3 hover:border-sea/40 transition"
            >
              <div>
                <div className="font-medium">{d.name}</div>
                <div className="text-xs text-ink-soft">
                  {d.status} · {d.workflowStatus}
                </div>
              </div>
              <HealthBadge health={d.latestHealth} score={d.latestScore} fit={d.latestFitForUse} />
            </Link>
          ))}
          {datasets.length === 0 && (
            <p className="text-ink-soft text-sm">
              No datasets yet. {isData ? 'Upload a CSV to begin.' : 'Waiting for Data User uploads.'}
            </p>
          )}
        </div>
      </section>
    </div>
  )
}

function Kpi({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-xl border border-mist bg-white/80 p-4">
      <div className="text-xs uppercase tracking-wide text-ink-soft">{label}</div>
      <div className="font-display text-3xl mt-1">{value}</div>
    </div>
  )
}
