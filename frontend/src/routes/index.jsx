import { Routes, Route } from 'react-router-dom'
import DashboardPage from '../features/dashboard/DashboardPage.jsx'
import LogsPage from '../features/logs/LogsPage.jsx'
import AlertsPage from '../features/alerts/AlertsPage.jsx'
import SettingsPage from '../features/settings/SettingsPage.jsx'

export default function AppRoutes() {
  return (
    <Routes>
      <Route path="/" element={<DashboardPage />} />
      <Route path="/logs" element={<LogsPage />} />
      <Route path="/alerts" element={<AlertsPage />} />
      <Route path="/settings" element={<SettingsPage />} />
    </Routes>
  )
}
