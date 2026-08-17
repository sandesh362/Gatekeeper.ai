import { Link, useLocation } from 'react-router-dom'
import { useAppStore } from '../store/index.js'

const navItems = [
  { to: '/dashboard', label: 'Dashboard' }, { to: '/logs', label: 'Logs' },
  { to: '/alerts', label: 'Alerts' }, { to: '/settings', label: 'Settings' },
]

export default function AppShell({ children }) {
  const location = useLocation()
  const connectionStatus = useAppStore((state) => state.connectionStatus)
  const connected = connectionStatus === 'connected'
  return <div className="flex min-h-screen bg-slate-950">
    <aside className="hidden w-60 shrink-0 border-r border-slate-800 bg-slate-900/60 p-5 md:block">
      <div className="mb-10 flex items-center gap-3"><div className="flex h-9 w-9 items-center justify-center rounded-lg bg-gatekeeper-600 font-bold">G</div><div><h1 className="font-semibold">Gatekeeper.ai</h1><p className="text-xs text-slate-500">SECURITY CONSOLE</p></div></div>
      <nav className="space-y-1">{navItems.map(({ to, label }) => <Link key={to} to={to} className={`block rounded-md px-3 py-2 text-sm ${location.pathname === to || (to === '/logs' && location.pathname.startsWith('/logs/')) ? 'bg-gatekeeper-600 text-white' : 'text-slate-400 hover:bg-slate-800 hover:text-white'}`}>{label}</Link>)}</nav>
    </aside>
    <div className="flex min-w-0 flex-1 flex-col"><header className="border-b border-slate-800 bg-slate-900/80 px-6 py-4"><div className="flex items-center justify-between"><div className="md:hidden font-semibold">Gatekeeper.ai</div><div className="hidden text-xs text-slate-500 md:block">PROMPT-INJECTION FIREWALL</div><div className={`flex items-center gap-2 text-xs ${connected ? 'text-emerald-400' : 'text-amber-400'}`}><span className={`h-2 w-2 rounded-full ${connected ? 'bg-emerald-400' : 'bg-amber-400'}`} />LIVE {connectionStatus}</div></div></header><main className="w-full flex-1 px-6 py-6">{children}</main></div>
  </div>
}
