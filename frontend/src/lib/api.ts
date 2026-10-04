import axios from 'axios'
import { config } from '../config'
import type { Alert, AiSummary, Dataset, DqRun, Issue } from '../types'

let authToken = ''
let devRole = 'DataUser'
let devSub = 'dev-user'
let devEmail = 'dev@example.com'

export function setApiAuth(opts: {
  token: string
  role?: string
  sub?: string
  email?: string
}) {
  authToken = opts.token
  if (opts.role) devRole = opts.role
  if (opts.sub) devSub = opts.sub
  if (opts.email) devEmail = opts.email
}

const client = axios.create({
  baseURL: config.apiBaseUrl,
  timeout: 120000,
})

client.interceptors.request.use((req) => {
  req.headers = req.headers || {}
  if (authToken) {
    req.headers.Authorization = `Bearer ${authToken}`
  }
  if (config.devAuth) {
    req.headers['X-Dev-Role'] = devRole
    req.headers['X-Dev-Sub'] = devSub
    req.headers['X-Dev-Email'] = devEmail
  }
  return req
})

export async function getUploadUrl(filename: string) {
  const { data } = await client.post<{
    datasetId: string
    uploadUrl: string
    s3Key: string
  }>('/datasets/upload-url', { filename, contentType: 'text/csv' })
  return data
}

export async function uploadToS3(uploadUrl: string, file: File) {
  await axios.put(uploadUrl, file, {
    headers: { 'Content-Type': 'text/csv' },
  })
}

export async function registerDataset(payload: {
  datasetId: string
  s3Key: string
  name: string
  filename: string
}) {
  const { data } = await client.post<Dataset>('/datasets', payload)
  return data
}

export async function listDatasets() {
  const { data } = await client.get<{ datasets: Dataset[] }>('/datasets')
  return data.datasets
}

export async function getDataset(id: string) {
  const { data } = await client.get<Dataset>(`/datasets/${id}`)
  return data
}

export async function analyzeDataset(id: string, body?: { s3Key?: string }) {
  const { data } = await client.post<{ dataset: Dataset; run: DqRun }>(
    `/datasets/${id}/analyze`,
    body || {},
  )
  return data
}

export async function getRuns(id: string) {
  const { data } = await client.get<{ runs: DqRun[] }>(`/datasets/${id}/runs`)
  return data.runs
}

export async function getReport(id: string) {
  const { data } = await client.get<{
    dataset: Dataset
    run: DqRun
    issues: Issue[]
  }>(`/datasets/${id}/report`)
  return data
}

export async function exportReport(id: string) {
  const { data } = await client.get<{
    filename: string
    contentType: string
    content: string
  }>(`/datasets/${id}/export`)
  return data
}

export async function getAiSummary(id: string) {
  const { data } = await client.post<AiSummary>(`/datasets/${id}/summary`, {})
  return data
}

export async function listIssues(id: string) {
  const { data } = await client.get<{ issues: Issue[] }>(`/datasets/${id}/issues`)
  return data.issues
}

export async function enterCorrection(id: string, note?: string) {
  const { data } = await client.post<Dataset>(`/datasets/${id}/correction`, { note })
  return data
}

export async function createAlert(datasetId: string, note: string, force = false) {
  const { data } = await client.post<Alert>('/alerts', { datasetId, note, force })
  return data
}

export async function listAlerts() {
  const { data } = await client.get<{ alerts: Alert[] }>('/alerts')
  return data.alerts
}

export async function issueAction(
  issueId: string,
  action: 'assign' | 'acknowledge' | 'resolve' | 'reopen',
  datasetId: string,
  note?: string,
) {
  const { data } = await client.post<Issue>(`/issues/${issueId}/${action}`, {
    datasetId,
    note,
  })
  return data
}
