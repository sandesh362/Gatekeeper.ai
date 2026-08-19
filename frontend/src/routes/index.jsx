import { Navigate, Routes, Route } from 'react-router-dom'
import DashboardPage from '../features/dashboard/DashboardPage.jsx'
import LogsPage from '../features/logs/LogsPage.jsx'
import AlertsPage from '../features/alerts/AlertsPage.jsx'
import SettingsPage from '../features/settings/SettingsPage.jsx'
import RequestDetailPage from '../features/logs/RequestDetailPage.jsx'
import { LoginPage, ProtectedRoute, RegisterPage } from '../features/auth/index.jsx'

export default function AppRoutes() {
  return (
    <Routes>
      <Route path="/" element={<Navigate to="/dashboard" replace />} />
      <Route path="/login" element={<LoginPage />} /><Route path="/register" element={<RegisterPage />} />
      <Route path="/dashboard" element={<ProtectedRoute><DashboardPage /></ProtectedRoute>} />
      <Route path="/logs" element={<ProtectedRoute><LogsPage /></ProtectedRoute>} /><Route path="/logs/:id" element={<ProtectedRoute><RequestDetailPage /></ProtectedRoute>} />
      <Route path="/alerts" element={<ProtectedRoute><AlertsPage /></ProtectedRoute>} /><Route path="/settings" element={<ProtectedRoute><SettingsPage /></ProtectedRoute>} />
    </Routes>
  )
}
