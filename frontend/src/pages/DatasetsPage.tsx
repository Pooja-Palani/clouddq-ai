import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { listDatasets } from '../lib/api'
import type { Dataset } from '../types'
import { HealthBadge } from '../components/Badges'
import { useAuth } from '../auth/AuthContext'

const SAMPLES = [
  { name: 'Customers (dirty)', file: 'customers_dirty.csv', hint: 'Duplicates, bad emails, future dates' },
  { name: 'Orders (dirty)', file: 'orders_dirty.csv', hint: 'Negative prices, case inconsistency' },
  { name: 'Employees (clean)', file: 'employees_clean.csv', hint: 'Healthy baseline dataset' },
]

export function DatasetsPage() {
  const { user } = useAuth()
  const [datasets, setDatasets] = useState<Dataset[]>([])
  const [error, setError] = useState('')

  useEffect(() => {
    listDatasets()
      .then(setDatasets)
      .catch((e) => setError(e instanceof Error ? e.message : 'Failed to load'))
  }, [])

  return (
    <div className="space-y-8">
      <div className="flex items-end justify-between gap-4 flex-wrap">
        <div>
          <h1 className="font-display text-3xl">Dataset repository</h1>
          <p className="text-ink-soft text-sm mt-1">Status timeline, scores, and historical runs</p>
        </div>
        {user?.role === 'DataUser' && (
          <Link to="/app/upload" className="rounded-md bg-sea text-white px-4 py-2 text-sm font-medium">
            Upload new
          </Link>
        )}
      </div>

      {error && <p className="text-coral text-sm">{error}</p>}

      <div className="overflow-x-auto rounded-xl border border-mist bg-white/80">
        <table className="w-full text-sm">
          <thead className="bg-mist/50 text-left">
            <tr>
              <th className="px-4 py-3">Name</th>
              <th className="px-4 py-3">Status</th>
              <th className="px-4 py-3">Workflow</th>
              <th className="px-4 py-3">Quality</th>
              <th className="px-4 py-3"></th>
            </tr>
          </thead>
          <tbody>
            {datasets.map((d) => (
              <tr key={d.datasetId} className="border-t border-mist">
                <td className="px-4 py-3 font-medium">{d.name}</td>
                <td className="px-4 py-3">{d.status}</td>
                <td className="px-4 py-3">{d.workflowStatus}</td>
                <td className="px-4 py-3">
                  <HealthBadge health={d.latestHealth} score={d.latestScore} fit={d.latestFitForUse} />
                </td>
                <td className="px-4 py-3 text-right">
                  <Link to={`/app/datasets/${d.datasetId}`} className="text-sea font-medium hover:underline">
                    Open
                  </Link>
                </td>
              </tr>
            ))}
            {datasets.length === 0 && (
              <tr>
                <td colSpan={5} className="px-4 py-8 text-center text-ink-soft">
                  No datasets registered yet.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      <section>
        <h2 className="font-display text-xl mb-3">Sample dirty datasets</h2>
        <p className="text-sm text-ink-soft mb-4">
          Download from the repo <code className="text-sea">samples/</code> folder, then upload as a Data User.
        </p>
        <div className="grid sm:grid-cols-3 gap-3">
          {SAMPLES.map((s) => (
            <div key={s.file} className="rounded-xl border border-mist bg-white/80 p-4">
              <div className="font-medium">{s.name}</div>
              <div className="text-xs text-ink-soft mt-1">{s.hint}</div>
              <div className="text-xs mt-2 font-mono text-sea">{s.file}</div>
            </div>
          ))}
        </div>
      </section>
    </div>
  )
}
