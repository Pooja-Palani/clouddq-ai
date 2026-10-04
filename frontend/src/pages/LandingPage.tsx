import { Link } from 'react-router-dom'
import { useAuth } from '../auth/AuthContext'

export function LandingPage() {
  const { user } = useAuth()
  return (
    <div className="min-h-screen relative overflow-hidden">
      <div
        className="absolute inset-0 -z-10"
        style={{
          background:
            'radial-gradient(ellipse 80% 60% at 20% 10%, #248f7a33, transparent), radial-gradient(ellipse 70% 50% at 90% 20%, #c4922a22, transparent), linear-gradient(160deg, #f3f7f4 0%, #dce8e1 45%, #e8f0ec 100%)',
        }}
      />
      <div
        className="absolute inset-0 -z-10 opacity-40"
        style={{
          backgroundImage:
            'url("data:image/svg+xml,%3Csvg width=\'60\' height=\'60\' viewBox=\'0 0 60 60\' xmlns=\'http://www.w3.org/2000/svg\'%3E%3Cg fill=\'none\' fill-rule=\'evenodd\'%3E%3Cg fill=\'%231a6b5c\' fill-opacity=\'0.06\'%3E%3Cpath d=\'M36 34v-4h-2v4h-4v2h4v4h2v-4h4v-2h-4zm0-30V0h-2v4h-4v2h4v4h2V6h4V4h-4zM6 34v-4H4v4H0v2h4v4h2v-4h4v-2H6zM6 4V0H4v4H0v2h4v4h2V6h4V4H6z\'/%3E%3C/g%3E%3C/g%3E%3C/svg%3E")',
        }}
      />

      <header className="mx-auto max-w-6xl px-4 py-6 flex justify-between items-center">
        <span className="font-display text-2xl text-sea">CloudDQ AI</span>
        <Link
          to={user ? '/app' : '/login'}
          className="rounded-md bg-sea px-4 py-2 text-white text-sm font-medium hover:bg-sea-bright transition"
        >
          {user ? 'Open app' : 'Sign in'}
        </Link>
      </header>

      <section className="mx-auto max-w-6xl px-4 pt-16 pb-24 grid lg:grid-cols-2 gap-12 items-center">
        <div className="space-y-6 animate-[fadeUp_0.7s_ease]">
          <p className="font-display text-5xl sm:text-6xl leading-tight text-ink">
            CloudDQ AI
          </p>
          <h1 className="text-xl sm:text-2xl text-ink-soft font-medium max-w-lg">
            Explainable, serverless data-quality assessment for CSV datasets — scored across six dimensions, with AI executive insights.
          </h1>
          <p className="text-ink-soft max-w-md">
            Upload. Analyze. Visualize. Alert. Correct. Built on eight AWS services for Data Users and Business Users.
          </p>
          <div className="flex flex-wrap gap-3">
            <Link
              to="/login"
              className="rounded-md bg-sea px-5 py-3 text-white font-medium hover:bg-sea-bright transition shadow-sm"
            >
              Get started
            </Link>
            <a
              href="#how"
              className="rounded-md border border-sea/30 px-5 py-3 text-sea font-medium hover:bg-white/60 transition"
            >
              How it works
            </a>
          </div>
        </div>

        <div className="relative animate-[fadeIn_1s_ease]">
          <div className="rounded-2xl bg-ink text-foam p-6 shadow-xl rotate-1 hover:rotate-0 transition duration-500">
            <div className="text-xs uppercase tracking-widest text-mist/80 mb-4">Live quality pulse</div>
            <div className="font-display text-5xl mb-2">87%</div>
            <div className="text-sea-bright mb-6">HEALTHY · Fit for Analytics</div>
            <div className="grid grid-cols-3 gap-3 text-sm">
              {[
                ['Completeness', '94'],
                ['Validity', '88'],
                ['Uniqueness', '91'],
                ['Consistency', '85'],
                ['Accuracy', '82'],
                ['Timeliness', '79'],
              ].map(([k, v]) => (
                <div key={k} className="rounded-lg bg-white/5 p-3">
                  <div className="text-mist/70 text-xs">{k}</div>
                  <div className="font-semibold">{v}%</div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      <section id="how" className="bg-white/70 border-t border-mist py-16">
        <div className="mx-auto max-w-6xl px-4">
          <h2 className="font-display text-3xl mb-8">Login → Upload → Analyze → Report → AI → Alert</h2>
          <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-6 text-sm text-ink-soft">
            {[
              ['Six dimensions', 'Weighted Completeness, Validity, Uniqueness, Consistency, Accuracy, Timeliness.'],
              ['Role-aware SaaS', 'Data Users run quality; Business Users consume KPIs and raise alerts.'],
              ['Private by design', 'Presigned S3 uploads; Bedrock sees metrics JSON only — never raw CSV rows.'],
            ].map(([t, d]) => (
              <div key={t} className="border-l-2 border-sea pl-4">
                <div className="font-semibold text-ink mb-1">{t}</div>
                <p>{d}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      <style>{`
        @keyframes fadeUp { from { opacity: 0; transform: translateY(16px); } to { opacity: 1; transform: none; } }
        @keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }
      `}</style>
    </div>
  )
}
