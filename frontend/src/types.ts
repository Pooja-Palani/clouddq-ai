export type Role = 'DataUser' | 'BusinessUser'

export interface Dataset {
  datasetId: string
  name: string
  filename?: string
  s3Key?: string
  ownerId?: string
  ownerEmail?: string
  status?: string
  workflowStatus?: string
  timeline?: { status: string; at: string; note?: string }[]
  createdAt?: string
  updatedAt?: string
  runHistory?: { runId: string; at: string; dq_score: number; health: string }[]
  latestScore?: number | null
  latestHealth?: string | null
  latestFitForUse?: boolean
  latestSeverity?: { high: number; medium: number; low: number; total: number }
  latestRunId?: string
  latestDimensions?: Record<string, number>
  trend?: Trend
  alertId?: string | null
  aiSummary?: AiSummary | null
}

export interface Trend {
  runs: number
  direction: 'Improving' | 'Stable' | 'Declining' | 'Baseline' | 'NoData'
  trend_score: number | null
  slope_per_run?: number
  volatility?: number
  momentum?: number
  stability?: number
  change_total?: number
  change_last?: number
  forecast_next?: number
  best_score?: number
  worst_score?: number
  average_score?: number
  note?: string
}

export interface AiSummary {
  runId: string
  generatedAt: string
  executive_summary: string
  recommendations: string[]
  metrics_used?: Record<string, unknown>
  model?: string
}

export interface DqRun {
  runId: string
  datasetId: string
  createdAt: string
  dq_score: number
  health: string
  fit_for_analytics: boolean
  fit_for_use: boolean
  dimensions: Record<string, number>
  heatmap: { column: string; score: number; label: string; null_rate: number; type: string }[]
  issues: Issue[]
  severity: { high: number; medium: number; low: number; total: number }
  anomalies: { type: string; message: string }[]
  null_rate: number
  record_count: number
  rule_coverage?: { rules_evaluated: number; rules_failed: number }
  pii_hints?: { column: string; type: string }[]
  profile?: { record_count: number; column_count: number; columns: string[] }
}

export interface Issue {
  issue_id: string
  rule_name: string
  dimension: string
  severity: string
  status: string
  message: string
  threshold?: number
  current_score?: number
  history?: { status: string; at: string; note?: string; by?: string }[]
  assignedTo?: string
  column?: string
}

export interface Alert {
  alertId: string
  datasetId: string
  datasetName?: string
  note: string
  status: string
  dqScore?: number
  health?: string
  fromEmail?: string
  toUserId?: string
  createdAt: string
  history?: { status: string; at: string; note?: string; by?: string }[]
}
