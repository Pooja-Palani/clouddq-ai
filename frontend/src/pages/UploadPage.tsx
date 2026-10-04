import { useState, type FormEvent } from 'react'
import { useNavigate } from 'react-router-dom'
import { analyzeDataset, getUploadUrl, registerDataset, uploadToS3 } from '../lib/api'
import { config } from '../config'

export function UploadPage() {
  const navigate = useNavigate()
  const [file, setFile] = useState<File | null>(null)
  const [name, setName] = useState('')
  const [busy, setBusy] = useState(false)
  const [step, setStep] = useState('')
  const [error, setError] = useState('')
  const [autoAnalyze, setAutoAnalyze] = useState(true)

  async function onSubmit(e: FormEvent) {
    e.preventDefault()
    if (!file) return
    setBusy(true)
    setError('')
    try {
      setStep('Requesting presigned upload URL…')
      const { datasetId, uploadUrl, s3Key } = await getUploadUrl(file.name)

      if (config.devAuth && uploadUrl.includes('amazonaws.com') === false) {
        // Local mock path handled by backend mock if present
      }

      setStep('Uploading CSV directly to S3…')
      try {
        await uploadToS3(uploadUrl, file)
      } catch (uploadErr) {
        if (!config.devAuth) throw uploadErr
        // In pure local mock without S3, registration may still work if backend stores inline — skip
        console.warn('S3 upload failed in dev; continuing if backend allows', uploadErr)
      }

      setStep('Registering dataset…')
      const ds = await registerDataset({
        datasetId,
        s3Key,
        name: name || file.name.replace(/\.csv$/i, ''),
        filename: file.name,
      })

      if (autoAnalyze) {
        setStep('Running DQ analysis…')
        await analyzeDataset(ds.datasetId)
      }

      navigate(`/app/datasets/${ds.datasetId}`)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Upload failed')
    } finally {
      setBusy(false)
      setStep('')
    }
  }

  return (
    <div className="max-w-xl space-y-6">
      <div>
        <h1 className="font-display text-3xl">Upload CSV</h1>
        <p className="text-ink-soft text-sm mt-1">
          Browser never receives AWS keys — uploads use short-lived presigned S3 URLs.
        </p>
      </div>

      <form onSubmit={onSubmit} className="rounded-xl border border-mist bg-white/80 p-6 space-y-4">
        <label className="block text-sm">
          <span className="font-medium">Display name</span>
          <input
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="Customer Master"
            className="mt-1 w-full rounded-md border border-mist px-3 py-2"
          />
        </label>
        <label className="block text-sm">
          <span className="font-medium">CSV file</span>
          <input
            type="file"
            accept=".csv,text/csv"
            required
            onChange={(e) => setFile(e.target.files?.[0] || null)}
            className="mt-1 w-full text-sm"
          />
        </label>
        <label className="flex items-center gap-2 text-sm">
          <input
            type="checkbox"
            checked={autoAnalyze}
            onChange={(e) => setAutoAnalyze(e.target.checked)}
          />
          Run DQ analysis immediately after upload
        </label>
        {step && <p className="text-sm text-sea">{step}</p>}
        {error && <p className="text-sm text-coral">{error}</p>}
        <button
          type="submit"
          disabled={busy || !file}
          className="rounded-md bg-sea text-white px-4 py-2 font-medium disabled:opacity-60"
        >
          {busy ? 'Working…' : 'Upload'}
        </button>
      </form>
    </div>
  )
}
