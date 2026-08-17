import { useNavigate } from 'react-router-dom'

export function DecisionBadge({ decision }) {
  const styles = { pass: 'bg-emerald-500/15 text-emerald-300', flag: 'bg-amber-500/15 text-amber-300', block: 'bg-red-500/15 text-red-300', error: 'bg-slate-500/15 text-slate-300' }
  return <span className={`rounded px-2 py-1 text-xs font-semibold uppercase ${styles[decision] ?? styles.error}`}>{decision}</span>
}

export default function RequestTable({ items, acknowledged = {}, onToggleAcknowledged }) {
  const navigate = useNavigate()
  if (!items.length) return <div className="rounded-lg border border-slate-800 p-10 text-center text-sm text-slate-500">No requests match these filters.</div>
  return <div className="overflow-x-auto rounded-lg border border-slate-800"><table className="w-full text-left text-sm"><thead className="bg-slate-900 text-xs uppercase text-slate-500"><tr>{onToggleAcknowledged && <th className="px-3 py-3">Ack</th>}<th className="px-3 py-3">Timestamp</th><th className="px-3 py-3">Provider / model</th><th className="px-3 py-3">Decision</th><th className="px-3 py-3">Risk</th><th className="px-3 py-3">Latency</th><th className="px-3 py-3">Client</th></tr></thead><tbody>{items.map((item) => <tr key={item.id} onClick={() => navigate(`/logs/${item.id}`)} className="cursor-pointer border-t border-slate-800 hover:bg-slate-900/80">{onToggleAcknowledged && <td className="px-3 py-3" onClick={(event) => event.stopPropagation()}><input aria-label={`Acknowledge ${item.id}`} type="checkbox" checked={Boolean(acknowledged[item.id])} onChange={() => onToggleAcknowledged(item.id)} /></td>}<td className="whitespace-nowrap px-3 py-3 text-slate-400">{new Date(item.timestamp).toLocaleString()}</td><td className="px-3 py-3"><div>{item.provider}</div><div className="max-w-36 truncate text-xs text-slate-500">{item.model}</div></td><td className="px-3 py-3"><DecisionBadge decision={item.decision} /></td><td className="px-3 py-3 font-mono">{item.risk_score ?? '—'}</td><td className="px-3 py-3">{item.latency_ms} ms</td><td className="px-3 py-3 text-slate-400">{item.client_id ?? '—'}</td></tr>)}</tbody></table></div>
}
