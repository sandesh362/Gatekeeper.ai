import { BrowserRouter } from 'react-router-dom'
import AppRoutes from './routes/index.jsx'
import AppShell from './components/AppShell.jsx'

export default function App() {
  return (
    <BrowserRouter>
      <AppShell>
        <AppRoutes />
      </AppShell>
    </BrowserRouter>
  )
}
