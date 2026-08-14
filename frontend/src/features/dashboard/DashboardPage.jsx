import { useBackendHealth } from '../../hooks/useBackendHealth.js'

export default function DashboardPage() {
  const { loading, ok, data, error } = useBackendHealth()

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-semibold">Dashboard</h2>
        <p className="mt-1 text-sm text-slate-400">
          Real-time overview of prompt-injection firewall activity.
        </p>
      </div>

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        <StatCard title="Requests Today" value="—" subtitle="Phase 2" />
        <StatCard title="Threats Blocked" value="—" subtitle="Phase 2" />
        <StatCard title="Backend Status" value={loading ? '…' : ok ? 'Online' : 'Offline'} subtitle={error ?? data?.service ?? 'gatekeeper'} />
      </div>

      <div className="rounded-xl border border-slate-800 bg-slate-900/50 p-6">
        <h3 className="font-medium text-slate-200">Phase 1 Scaffold</h3>
        <p className="mt-2 text-sm text-slate-400">
          Detection layers, proxy forwarding, and live metrics will be wired in Phase 2.
        </p>
      </div>
    </div>
  )
}

function StatCard({ title, value, subtitle }) {
  return (
    <div className="rounded-xl border border-slate-800 bg-slate-900/50 p-5">
      <p className="text-sm text-slate-400">{title}</p>
      <p className="mt-2 text-3xl font-semibold">{value}</p>
      <p className="mt-1 text-xs text-slate-500">{subtitle}</p>
    </div>
  )
}
