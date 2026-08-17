const API_BASE = import.meta.env.VITE_API_BASE_URL ?? ''

async function request(path, options = {}) {
  const response = await fetch(`${API_BASE}${path}`, { headers: { 'Content-Type': 'application/json', ...options.headers }, ...options })
  if (!response.ok) throw new Error(`API error: ${response.status} ${response.statusText}`)
  return response.json()
}

function queryString(filters = {}) {
  const params = new URLSearchParams()
  Object.entries(filters).forEach(([key, value]) => { if (value) params.set(key, value) })
  return params.toString() ? `?${params}` : ''
}

export const dashboardApi = {
  getRequests: (filters) => request(`/v1/dashboard/requests${queryString(filters)}`),
  getRequest: (id) => request(`/v1/dashboard/requests/${id}`),
  getStats: () => request('/v1/dashboard/stats'),
}

export function liveDashboardUrl() {
  const base = API_BASE || window.location.origin
  return `${base.replace(/^http/, 'ws')}/v1/dashboard/live`
}

export function healthCheck() { return request('/health') }
export function getApiV1Root() { return request('/api/v1/') }
