import { useState, type FormEvent } from 'react'
import { Link, Navigate, useNavigate } from 'react-router-dom'
import { useAuth } from '../auth/AuthContext'
import { config } from '../config'

export function LoginPage() {
  const { user, login } = useAuth()
  const navigate = useNavigate()
  const [email, setEmail] = useState(config.devAuth ? 'data@example.com' : '')
  const [password, setPassword] = useState(config.devAuth ? 'Password1' : '')
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)

  if (user) return <Navigate to="/app" replace />

  async function onSubmit(e: FormEvent) {
    e.preventDefault()
    setBusy(true)
    setError('')
    try {
      await login(email, password)
      navigate('/app')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Login failed')
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center px-4"
      style={{ background: 'linear-gradient(145deg, #f3f7f4, #dce8e1 60%, #c5ddd3)' }}>
      <div className="w-full max-w-md bg-white/90 backdrop-blur rounded-2xl shadow-lg border border-mist p-8">
        <Link to="/" className="font-display text-2xl text-sea">CloudDQ AI</Link>
        <h1 className="mt-4 text-xl font-semibold">Sign in</h1>
        <p className="text-sm text-ink-soft mt-1">
          Cognito roles: <strong>DataUser</strong> or <strong>BusinessUser</strong>
        </p>

        {config.devAuth && (
          <div className="mt-4 rounded-lg bg-amber/10 border border-amber/30 text-sm p-3 text-ink-soft">
            Dev auth is on. Use any password. Email containing <code>business</code> → BusinessUser; otherwise DataUser.
          </div>
        )}

        <form onSubmit={onSubmit} className="mt-6 space-y-4">
          <label className="block text-sm">
            <span className="font-medium">Email</span>
            <input
              type="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="mt-1 w-full rounded-md border border-mist px-3 py-2 focus:outline-none focus:ring-2 focus:ring-sea/40"
            />
          </label>
          <label className="block text-sm">
            <span className="font-medium">Password</span>
            <input
              type="password"
              required
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="mt-1 w-full rounded-md border border-mist px-3 py-2 focus:outline-none focus:ring-2 focus:ring-sea/40"
            />
          </label>
          {error && <p className="text-sm text-coral">{error}</p>}
          <button
            type="submit"
            disabled={busy}
            className="w-full rounded-md bg-sea text-white py-2.5 font-medium hover:bg-sea-bright disabled:opacity-60"
          >
            {busy ? 'Signing in…' : 'Sign in'}
          </button>
        </form>
      </div>
    </div>
  )
}
