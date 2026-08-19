import { useEffect, useState } from 'react'
import { authApi } from '../../services/api.js'
export default function SettingsPage() {
  const [keys,setKeys]=useState([]),[name,setName]=useState('Default SDK key'),[created,setCreated]=useState(''),[error,setError]=useState('')
  const load=()=>authApi.keys().then(setKeys).catch(()=>setError('Unable to load API keys.'))
  useEffect(load,[])
  async function create(){ try {const key=await authApi.createKey({name});setCreated(key.key);load()}catch{setError('Unable to create API key.')} }
  async function revoke(id){await authApi.revokeKey(id);load()}
  return <section className="space-y-5"><div><h2 className="text-2xl font-semibold">API keys</h2><p className="text-sm text-slate-400">Keys authenticate SDK requests for your organization.</p></div><div className="flex gap-2"><input className="rounded bg-slate-800 p-2" value={name} onChange={e=>setName(e.target.value)}/><button className="rounded bg-gatekeeper-600 px-3" onClick={create}>Create key</button></div>{created&&<div className="rounded border border-amber-500 bg-amber-950 p-4"><p className="font-semibold">Copy this key now — you will not see it again.</p><code className="block break-all py-2">{created}</code><button className="rounded bg-slate-700 px-3 py-1" onClick={()=>navigator.clipboard.writeText(created)}>Copy</button></div>}{error&&<p className="text-red-400">{error}</p>}<div className="max-w-2xl rounded border border-slate-800">{keys.map(k=><div key={k.id} className="flex items-center justify-between border-b border-slate-800 p-4"><span>{k.name} <code className="text-slate-400">{k.key_prefix}…</code></span><button className="text-red-400" onClick={()=>revoke(k.id)}>Revoke</button></div>)}</div></section>
}
