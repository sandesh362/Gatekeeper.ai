import { BrowserRouter } from 'react-router-dom'
import AppRoutes from './routes/index.jsx'
import AppShell from './components/AppShell.jsx'
import { useLiveDashboard } from './hooks/useLiveDashboard.js'

export default function App() {
  useLiveDashboard()
  return (
    <BrowserRouter>
      <AppShell>
        <AppRoutes />
      </AppShell>
    </BrowserRouter>
  )
}
