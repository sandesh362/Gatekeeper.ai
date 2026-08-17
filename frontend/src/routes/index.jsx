import { Navigate, Routes, Route } from 'react-router-dom'
import DashboardPage from '../features/dashboard/DashboardPage.jsx'
import LogsPage from '../features/logs/LogsPage.jsx'
import AlertsPage from '../features/alerts/AlertsPage.jsx'
import SettingsPage from '../features/settings/SettingsPage.jsx'
import RequestDetailPage from '../features/logs/RequestDetailPage.jsx'

export default function AppRoutes() {
  return (
    <Routes>
      <Route path="/" element={<Navigate to="/dashboard" replace />} />
      <Route path="/dashboard" element={<DashboardPage />} />
      <Route path="/logs" element={<LogsPage />} />
      <Route path="/logs/:id" element={<RequestDetailPage />} />
      <Route path="/alerts" element={<AlertsPage />} />
      <Route path="/settings" element={<SettingsPage />} />
    </Routes>
  )
}
