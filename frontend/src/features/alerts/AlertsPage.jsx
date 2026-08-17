import { useEffect, useState } from 'react'
import { dashboardApi } from '../../services/api.js'
import RequestTable from '../logs/RequestTable.jsx'

export default function AlertsPage() {
  const [items, setItems] = useState([]); const [acknowledged, setAcknowledged] = useState({})
  useEffect(() => { Promise.all([dashboardApi.getRequests({ decision: 'flag', page_size: 100 }), dashboardApi.getRequests({ decision: 'block', page_size: 100 })]).then(([flags, blocks]) => setItems([...flags.items, ...blocks.items].sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp)))) }, [])
  return <section className="space-y-5"><div><h2 className="text-2xl font-semibold">Alerts</h2><p className="text-sm text-slate-400">Flagged and blocked requests requiring attention.</p></div><RequestTable items={items} acknowledged={acknowledged} onToggleAcknowledged={(id) => setAcknowledged((current) => ({ ...current, [id]: !current[id] }))} /></section>
}
