import { useState } from 'react'
import { Link, Navigate, useNavigate } from 'react-router-dom'
import { authApi } from '../../services/api.js'
import { useAppStore } from '../../store/index.js'
function Form({ register = false }) {
  const navigate = useNavigate(); const setToken = useAppStore(s => s.setAccessToken); const [error,setError]=useState(''); const [form,setForm]=useState({ email:'',password:'',organization_name:'' })
  async function submit(e) { e.preventDefault(); try { const r=await (register?authApi.register(form):authApi.login(form)); window.__gatekeeperAccessToken=r.access_token; setToken(r.access_token); navigate('/dashboard') } catch { setError('Authentication failed. Check your details and try again.') } }
  return <main className="mx-auto mt-24 max-w-md rounded-lg border border-slate-800 bg-slate-900 p-6"><h1 className="mb-5 text-2xl font-semibold">{register?'Create account':'Sign in to Gatekeeper'}</h1><form onSubmit={submit} className="space-y-3">{register&&<input className="w-full rounded bg-slate-800 p-3" placeholder="Organization name" onChange={e=>setForm({...form,organization_name:e.target.value})}/>}<input className="w-full rounded bg-slate-800 p-3" type="email" placeholder="Email" onChange={e=>setForm({...form,email:e.target.value})}/><input className="w-full rounded bg-slate-800 p-3" type="password" placeholder="Password" onChange={e=>setForm({...form,password:e.target.value})}/>{error&&<p className="text-sm text-red-400">{error}</p>}<button className="w-full rounded bg-gatekeeper-600 p-3">{register?'Register':'Login'}</button></form><p className="mt-4 text-sm text-slate-400"><Link to={register?'/login':'/register'}>{register?'Already have an account? Login':'Need an account? Register'}</Link></p></main>
}
export const LoginPage=()=> <Form />
export const RegisterPage=()=> <Form register />
export function ProtectedRoute({children}) { const token=useAppStore(s=>s.accessToken); const ready=useAppStore(s=>s.authReady); if(!ready)return null; return token?children:<Navigate to="/login" replace/> }
