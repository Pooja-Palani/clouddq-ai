import { Link, NavLink, Outlet } from 'react-router-dom'
import { useAuth } from '../auth/AuthContext'

export function AppShell() {
  const { user, logout } = useAuth()
  const isData = user?.role === 'DataUser'

  const linkClass = ({ isActive }: { isActive: boolean }) =>
    `px-3 py-2 rounded-md text-sm font-medium transition ${
      isActive ? 'bg-sea text-white' : 'text-ink-soft hover:bg-mist'
    }`

  return (
    <div className="min-h-screen flex flex-col">
      <header className="no-print border-b border-mist bg-white/80 backdrop-blur sticky top-0 z-20">
        <div className="mx-auto max-w-6xl px-4 py-3 flex items-center justify-between gap-4">
          <Link to="/" className="font-display text-xl text-sea tracking-tight">
            CloudDQ AI
          </Link>
          <nav className="flex flex-wrap items-center gap-1">
            <NavLink to="/app" end className={linkClass}>
              Home
            </NavLink>
            <NavLink to="/app/datasets" className={linkClass}>
              Datasets
            </NavLink>
            {isData && (
              <NavLink to="/app/upload" className={linkClass}>
                Upload
              </NavLink>
            )}
            <NavLink to="/app/alerts" className={linkClass}>
              Alerts
            </NavLink>
          </nav>
          <div className="flex items-center gap-3 text-sm">
            <span className="hidden sm:inline text-ink-soft">
              {user?.email} · <strong className="text-sea">{user?.role}</strong>
            </span>
            <button
              type="button"
              onClick={logout}
              className="rounded-md border border-mist px-3 py-1.5 hover:bg-mist"
            >
              Sign out
            </button>
          </div>
        </div>
      </header>
      <main className="flex-1 mx-auto w-full max-w-6xl px-4 py-8">
        <Outlet />
      </main>
      <footer className="no-print border-t border-mist py-4 text-center text-xs text-ink-soft">
        Serverless data quality · Amplify · Cognito · API Gateway · Lambda · S3 · DynamoDB · CloudWatch · Bedrock
      </footer>
    </div>
  )
}
