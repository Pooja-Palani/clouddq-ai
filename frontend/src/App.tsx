import { Navigate, Outlet, Route, Routes } from 'react-router-dom'
import { AuthProvider, useAuth } from './auth/AuthContext'
import { AppShell } from './components/AppShell'
import { LandingPage } from './pages/LandingPage'
import { LoginPage } from './pages/LoginPage'
import { HomePage } from './pages/HomePage'
import { DatasetsPage } from './pages/DatasetsPage'
import { UploadPage } from './pages/UploadPage'
import { DatasetDetailPage } from './pages/DatasetDetailPage'
import { AlertsPage } from './pages/AlertsPage'

function Protected() {
  const { user, loading } = useAuth()
  if (loading) return <div className="p-8 text-ink-soft">Loading…</div>
  if (!user) return <Navigate to="/login" replace />
  return <Outlet />
}

function DataUserOnly() {
  const { user } = useAuth()
  if (user?.role !== 'DataUser') return <Navigate to="/app" replace />
  return <Outlet />
}

export default function App() {
  return (
    <AuthProvider>
      <Routes>
        <Route path="/" element={<LandingPage />} />
        <Route path="/login" element={<LoginPage />} />
        <Route element={<Protected />}>
          <Route path="/app" element={<AppShell />}>
            <Route index element={<HomePage />} />
            <Route path="datasets" element={<DatasetsPage />} />
            <Route path="datasets/:id" element={<DatasetDetailPage />} />
            <Route path="alerts" element={<AlertsPage />} />
            <Route element={<DataUserOnly />}>
              <Route path="upload" element={<UploadPage />} />
            </Route>
          </Route>
        </Route>
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </AuthProvider>
  )
}
