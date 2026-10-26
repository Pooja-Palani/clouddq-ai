import { useEffect, useMemo, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import {
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
  Bar,
  BarChart,
} from 'recharts'
import { useAuth } from '../auth/AuthContext'
import { HealthBadge, SeverityPills } from '../components/Badges'
import {
  analyzeDataset,
  createAlert,
  enterCorrection,
  exportReport,
  getAiSummary,
  getDataset,
  getReport,
  getUploadUrl,
  issueAction,
  uploadToS3,
} from '../lib/api'
import type { AiSummary, Dataset, DqRun, Issue } from '../types'

export function DatasetDetailPage() {
  const { id = '' } = useParams()
  const { user } = useAuth()
  const [dataset, setDataset] = useState<Dataset | null>(null)
  const [run, setRun] = useState<DqRun | null>(null)
  const [issues, setIssues] = useState<Issue[]>([])
  const [summary, setSummary] = useState<AiSummary | null>(null)
  const [error, setError] = useState('')
  const [busy, setBusy] = useState('')
  const [alertNote, setAlertNote] = useState('Quality below acceptable threshold — please investigate.')
  const [sevFilter, setSevFilter] = useState<'ALL' | 'HIGH' | 'MEDIUM' | 'LOW'>('ALL')

  async function refresh() {
    const ds = await getDataset(id)
    setDataset(ds)
    if (ds.latestRunId) {
      try {
        const report = await getReport(id)
        setRun(report.run)
        setIssues(report.issues)
      } catch {
        setRun(null)
        setIssues([])
      }
    }
    if (ds.aiSummary) setSummary(ds.aiSummary)
  }

  useEffect(() => {
    refresh().catch((e) => setError(e instanceof Error ? e.message : 'Load failed'))
  }, [id])

  const trend = useMemo(
    () =>
      (dataset?.runHistory || []).map((r, i) => ({
        name: `R${i + 1}`,
        score: r.dq_score,
      })),
    [dataset],
  )

  const dimData = useMemo(() => {
    const dims = run?.dimensions || dataset?.latestDimensions || {}
    return Object.entries(dims).map(([name, score]) => ({ name, score }))
  }, [run, dataset])

  const filteredIssues = issues.filter(
    (i) => sevFilter === 'ALL' || i.severity === sevFilter,
  )

  async function runAnalyze() {
    setBusy('Analyzing…')
    setError('')
    try {
      const res = await analyzeDataset(id)
      setDataset(res.dataset)
      setRun(res.run)
      setIssues(res.run.issues || [])
      setSummary(null)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Analyze failed')
    } finally {
      setBusy('')
    }
  }

  async function onExport() {
    const file = await exportReport(id)
    const blob = new Blob([file.content], { type: file.contentType })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = file.filename
    a.click()
    URL.revokeObjectURL(url)
  }

  async function onAiSummary() {
    setBusy('Generating AI summary…')
    try {
      const s = await getAiSummary(id)
      setSummary(s)
      await refresh()
    } catch (e) {
      setError(e instanceof Error ? e.message : 'AI summary failed')
    } finally {
      setBusy('')
    }
  }

  async function onAlert() {
    setBusy('Sending alert…')
    try {
      await createAlert(id, alertNote, true)
      await refresh()
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Alert failed')
    } finally {
      setBusy('')
    }
  }

  async function onCorrection() {
    setBusy('Entering correction…')
    try {
      await enterCorrection(id, 'Data user started correction flow')
      await refresh()
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed')
    } finally {
      setBusy('')
    }
  }

  async function onReupload(file: File) {
    setBusy('Re-uploading corrected CSV…')
    try {
      const { uploadUrl, s3Key } = await getUploadUrl(file.name)
      await uploadToS3(uploadUrl, file)
      // Keep same dataset id — update via analyze with new key
      await analyzeDataset(id, { s3Key })
      await refresh()
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Re-upload failed')
    } finally {
      setBusy('')
    }
  }

  async function onIssue(issue: Issue, action: 'acknowledge' | 'resolve' | 'reopen' | 'assign') {
    setBusy(`${action}…`)
    try {
      await issueAction(issue.issue_id, action, id)
      await refresh()
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Action failed')
    } finally {
      setBusy('')
    }
  }

  if (!dataset) {
    return <p className="text-ink-soft">{error || 'Loading…'}</p>
  }

  const isData = user?.role === 'DataUser'
  const isBiz = user?.role === 'BusinessUser'

  return (
    <div className="space-y-8">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <Link to="/app/datasets" className="text-sm text-sea hover:underline">
            ← Repository
          </Link>
          <h1 className="font-display text-3xl mt-1">{dataset.name}</h1>
          <p className="text-sm text-ink-soft">
            {dataset.filename} · Status {dataset.status} · Workflow {dataset.workflowStatus}
          </p>
        </div>
        <HealthBadge
          health={run?.health || dataset.latestHealth}
          score={run?.dq_score ?? dataset.latestScore}
          fit={run?.fit_for_use ?? dataset.latestFitForUse}
        />
      </div>

      {error && <p className="text-coral text-sm">{error}</p>}
      {busy && <p className="text-sea text-sm">{busy}</p>}

      <div className="no-print flex flex-wrap gap-2">
        {isData && (
          <button type="button" onClick={runAnalyze} className="rounded-md bg-sea text-white px-3 py-2 text-sm">
            Run / re-run analysis
          </button>
        )}
        <button type="button" onClick={onExport} className="rounded-md border border-mist px-3 py-2 text-sm">
          Export CSV report
        </button>
        <button type="button" onClick={() => window.print()} className="rounded-md border border-mist px-3 py-2 text-sm">
          Print report
        </button>
        <button type="button" onClick={onAiSummary} className="rounded-md border border-mist px-3 py-2 text-sm">
          AI executive summary
        </button>
        {isData && (
          <button type="button" onClick={onCorrection} className="rounded-md border border-mist px-3 py-2 text-sm">
            Move to correction
          </button>
        )}
      </div>

      {/* Timeline */}
      <section className="rounded-xl border border-mist bg-white/80 p-4">
        <h2 className="font-display text-lg mb-3">Status timeline</h2>
        <ol className="space-y-2 text-sm">
          {(dataset.timeline || []).map((t, i) => (
            <li key={i} className="flex gap-3">
              <span className="text-sea font-medium w-36 shrink-0">{t.status}</span>
              <span className="text-ink-soft">{t.note}</span>
              <span className="ml-auto text-xs text-ink-soft">{t.at}</span>
            </li>
          ))}
        </ol>
      </section>

      {/* Dimension charts */}
      {dimData.length > 0 && (
        <section className="grid lg:grid-cols-2 gap-4">
          <div className="rounded-xl border border-mist bg-white/80 p-4">
            <h2 className="font-display text-lg mb-3">Six dimensions</h2>
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={dimData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#dce8e1" />
                  <XAxis dataKey="name" tick={{ fontSize: 11 }} />
                  <YAxis domain={[0, 100]} />
                  <Tooltip />
                  <Bar dataKey="score" fill="#1a6b5c" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>
          <div className="rounded-xl border border-mist bg-white/80 p-4">
            <h2 className="font-display text-lg mb-3">DQ score trend</h2>
            <div className="h-64">
              {trend.length > 0 ? (
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={trend}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#dce8e1" />
                    <XAxis dataKey="name" />
                    <YAxis domain={[0, 100]} />
                    <Tooltip />
                    <Line type="monotone" dataKey="score" stroke="#c4922a" strokeWidth={3} dot={{ r: 5 }} />
                  </LineChart>
                </ResponsiveContainer>
              ) : (
                <p className="text-sm text-ink-soft">Run analysis more than once to see trends.</p>
              )}
            </div>
            {dataset.trend && (
              <div className="mt-3 grid grid-cols-2 sm:grid-cols-4 gap-2 text-sm">
                <div>
                  <p className="text-xs text-ink-soft">Trend score</p>
                  <p className="font-display text-xl">{dataset.trend.trend_score ?? '—'}</p>
                </div>
                <div>
                  <p className="text-xs text-ink-soft">Direction</p>
                  <p
                    className={
                      dataset.trend.direction === 'Improving'
                        ? 'text-sea font-medium'
                        : dataset.trend.direction === 'Declining'
                          ? 'text-coral font-medium'
                          : 'font-medium'
                    }
                  >
                    {dataset.trend.direction}
                  </p>
                </div>
                <div>
                  <p className="text-xs text-ink-soft">Slope / volatility</p>
                  <p>
                    {dataset.trend.slope_per_run ?? '—'} pp/run · σ {dataset.trend.volatility ?? '—'}
                  </p>
                </div>
                <div>
                  <p className="text-xs text-ink-soft">Next-run forecast</p>
                  <p>{dataset.trend.forecast_next ?? '—'}%</p>
                </div>
              </div>
            )}
          </div>
        </section>
      )}

      {/* Heatmap + severity */}
      {run && (
        <section className="grid lg:grid-cols-2 gap-4">
          <div className="rounded-xl border border-mist bg-white/80 p-4">
            <h2 className="font-display text-lg mb-3">Column quality heatmap</h2>
            <div className="space-y-2">
              {run.heatmap.map((h) => (
                <div key={h.column} className="flex items-center gap-3 text-sm">
                  <span className="w-36 truncate font-medium">{h.column}</span>
                  <div className="flex-1 h-3 rounded-full bg-mist overflow-hidden">
                    <div
                      className="h-full rounded-full transition-all"
                      style={{
                        width: `${h.score}%`,
                        background:
                          h.score >= 90 ? '#2d7a4f' : h.score >= 80 ? '#1a6b5c' : h.score >= 60 ? '#c4922a' : '#c45c3e',
                      }}
                    />
                  </div>
                  <span className="w-20 text-right text-xs">{h.label}</span>
                </div>
              ))}
            </div>
          </div>
          <div className="rounded-xl border border-mist bg-white/80 p-4 space-y-3">
            <h2 className="font-display text-lg">Severity & coverage</h2>
            <SeverityPills severity={run.severity} />
            <p className="text-sm text-ink-soft">
              Rules evaluated: {run.rule_coverage?.rules_evaluated ?? '—'} · Failed:{' '}
              {run.rule_coverage?.rules_failed ?? '—'}
            </p>
            {run.pii_hints && run.pii_hints.length > 0 && (
              <div>
                <div className="text-xs uppercase tracking-wide text-ink-soft mb-1">PII hints</div>
                <ul className="text-sm space-y-1">
                  {run.pii_hints.map((p) => (
                    <li key={p.column}>
                      {p.column} <span className="text-ink-soft">({p.type})</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}
            {run.anomalies?.length > 0 && (
              <div>
                <div className="text-xs uppercase tracking-wide text-ink-soft mb-1">Anomalies</div>
                <ul className="text-sm space-y-1">
                  {run.anomalies.map((a, i) => (
                    <li key={i} className="text-amber">
                      {a.message}
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        </section>
      )}

      {/* AI summary */}
      <section className="rounded-xl border border-mist bg-white/80 p-4">
        <h2 className="font-display text-lg mb-2">AI executive summary</h2>
        {summary ? (
          <div className="space-y-3 text-sm">
            <p className="leading-relaxed">{summary.executive_summary}</p>
            <div>
              <div className="font-semibold mb-1">Top 3 recommendations</div>
              <ol className="list-decimal pl-5 space-y-1">
                {summary.recommendations.map((r, i) => (
                  <li key={i}>{r}</li>
                ))}
              </ol>
            </div>
            <p className="text-xs text-ink-soft">
              Model {summary.model} · metrics JSON only (no raw CSV) · {summary.generatedAt}
            </p>
          </div>
        ) : (
          <p className="text-sm text-ink-soft">Generate a Bedrock summary from aggregated quality metrics.</p>
        )}
      </section>

      {/* Business alert */}
      {isBiz && (
        <section className="no-print rounded-xl border border-coral/30 bg-coral/5 p-4 space-y-3">
          <h2 className="font-display text-lg">Send quality alert</h2>
          <textarea
            value={alertNote}
            onChange={(e) => setAlertNote(e.target.value)}
            className="w-full rounded-md border border-mist px-3 py-2 text-sm"
            rows={3}
          />
          <button type="button" onClick={onAlert} className="rounded-md bg-coral text-white px-4 py-2 text-sm">
            Alert Data User
          </button>
        </section>
      )}

      {/* Correction re-upload */}
      {isData && (dataset.workflowStatus === 'InCorrection' || dataset.workflowStatus === 'AlertRaised') && (
        <section className="no-print rounded-xl border border-amber/30 bg-amber/5 p-4 space-y-3">
          <h2 className="font-display text-lg">Soft correction — re-upload CSV</h2>
          <input
            type="file"
            accept=".csv"
            onChange={(e) => {
              const f = e.target.files?.[0]
              if (f) void onReupload(f)
            }}
          />
        </section>
      )}

      {/* Issues */}
      <section className="rounded-xl border border-mist bg-white/80 p-4">
        <div className="flex flex-wrap items-center justify-between gap-3 mb-3">
          <h2 className="font-display text-lg">Issues</h2>
          <div className="flex gap-1 text-xs">
            {(['ALL', 'HIGH', 'MEDIUM', 'LOW'] as const).map((s) => (
              <button
                key={s}
                type="button"
                onClick={() => setSevFilter(s)}
                className={`px-2 py-1 rounded ${sevFilter === s ? 'bg-sea text-white' : 'bg-mist'}`}
              >
                {s}
              </button>
            ))}
          </div>
        </div>
        <div className="space-y-3">
          {filteredIssues.map((issue) => (
            <div key={issue.issue_id} className="border border-mist rounded-lg p-3 text-sm">
              <div className="flex flex-wrap justify-between gap-2">
                <div>
                  <span
                    className={`text-xs font-semibold mr-2 ${
                      issue.severity === 'HIGH'
                        ? 'text-coral'
                        : issue.severity === 'MEDIUM'
                          ? 'text-amber'
                          : 'text-sea'
                    }`}
                  >
                    {issue.severity}
                  </span>
                  <span className="font-medium">{issue.rule_name}</span>
                  <span className="text-ink-soft"> · {issue.status}</span>
                </div>
                {isData && (
                  <div className="no-print flex gap-2">
                    {issue.status === 'OPEN' && (
                      <button type="button" className="text-sea underline" onClick={() => onIssue(issue, 'acknowledge')}>
                        Acknowledge
                      </button>
                    )}
                    {issue.status !== 'RESOLVED' && (
                      <button type="button" className="text-sea underline" onClick={() => onIssue(issue, 'resolve')}>
                        Resolve
                      </button>
                    )}
                    {issue.status === 'RESOLVED' && (
                      <button type="button" className="text-sea underline" onClick={() => onIssue(issue, 'reopen')}>
                        Reopen
                      </button>
                    )}
                  </div>
                )}
              </div>
              <p className="mt-1 text-ink-soft">{issue.message}</p>
              {issue.history && issue.history.length > 0 && (
                <details className="mt-2 text-xs text-ink-soft">
                  <summary>Audit history</summary>
                  <ul className="mt-1 space-y-1 pl-2">
                    {issue.history.map((h, i) => (
                      <li key={i}>
                        {h.status} — {h.note} ({h.at})
                      </li>
                    ))}
                  </ul>
                </details>
              )}
            </div>
          ))}
          {filteredIssues.length === 0 && <p className="text-ink-soft text-sm">No issues for this filter.</p>}
        </div>
      </section>
    </div>
  )
}
