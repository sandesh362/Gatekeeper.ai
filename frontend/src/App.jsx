import { BrowserRouter } from 'react-router-dom'
import AppRoutes from './routes/index.jsx'
import AppShell from './components/AppShell.jsx'
import { useLiveDashboard } from './hooks/useLiveDashboard.js'
import { useEffect } from 'react'
import { authApi } from './services/api.js'
import { useAppStore } from './store/index.js'

export default function App() {
  useLiveDashboard()
  const setToken = useAppStore(s => s.setAccessToken)
  const clearSession = useAppStore(s => s.clearSession)
  useEffect(() => { authApi.refresh().then(r => { window.__gatekeeperAccessToken=r.access_token; setToken(r.access_token) }).catch(clearSession) }, [setToken, clearSession])
  return (
    <BrowserRouter>
      <AppShell>
        <AppRoutes />
      </AppShell>
    </BrowserRouter>
  )
}
