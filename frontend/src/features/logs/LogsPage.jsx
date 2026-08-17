import { useEffect, useState } from 'react'
import { dashboardApi } from '../../services/api.js'
import { useAppStore } from '../../store/index.js'
import RequestTable from './RequestTable.jsx'

export default function LogsPage() {
  const filters = useAppStore((state) => state.logFilters); const setFilters = useAppStore((state) => state.setLogFilters)
  const [data, setData] = useState({ items: [], total: 0 }); const [error, setError] = useState(''); const [page, setPage] = useState(1)
  useEffect(() => { dashboardApi.getRequests({ ...filters, page, page_size: 25 }).then(setData).catch((e) => setError(e.message)) }, [filters, page])
  const update = (key, value) => { setPage(1); setFilters({ ...filters, [key]: value }) }
  return <section className="space-y-5"><div><h2 className="text-2xl font-semibold">Request logs</h2><p className="text-sm text-slate-400">Complete proxy and detection audit trail.</p></div><div className="flex flex-wrap gap-3 rounded-lg border border-slate-800 bg-slate-900/50 p-3"><select value={filters.decision} onChange={(e) => update('decision', e.target.value)}><option value="">All decisions</option><option value="pass">Pass</option><option value="flag">Flag</option><option value="block">Block</option></select><select value={filters.provider} onChange={(e) => update('provider', e.target.value)}><option value="">All providers</option><option value="openai">OpenAI</option><option value="anthropic">Anthropic</option></select><input type="datetime-local" aria-label="Start date" value={filters.start} onChange={(e) => update('start', e.target.value)} /><input type="datetime-local" aria-label="End date" value={filters.end} onChange={(e) => update('end', e.target.value)} /></div>{error && <p className="text-sm text-red-300">{error}</p>}<RequestTable items={data.items} /><div className="flex items-center justify-between text-sm text-slate-400"><span>{data.total} requests</span><div className="space-x-2"><button disabled={page === 1} onClick={() => setPage(page - 1)}>Previous</button><span>Page {page}</span><button disabled={data.items.length < 25} onClick={() => setPage(page + 1)}>Next</button></div></div></section>
}
