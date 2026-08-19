const API_BASE = import.meta.env.VITE_API_BASE_URL ?? ''

async function request(path, options = {}) {
  const token = window.__gatekeeperAccessToken
  const response = await fetch(`${API_BASE}${path}`, { credentials: 'include', headers: { 'Content-Type': 'application/json', ...(token ? { Authorization: `Bearer ${token}` } : {}), ...options.headers }, ...options })
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
export const authApi = {
  register: (body) => request('/v1/auth/register', { method: 'POST', body: JSON.stringify(body) }),
  login: (body) => request('/v1/auth/login', { method: 'POST', body: JSON.stringify(body) }),
  refresh: () => request('/v1/auth/refresh', { method: 'POST' }),
  keys: () => request('/v1/api-keys'),
  createKey: (body) => request('/v1/api-keys', { method: 'POST', body: JSON.stringify(body) }),
  revokeKey: (id) => request(`/v1/api-keys/${id}`, { method: 'DELETE' }),
}

export function liveDashboardUrl(accessToken) {
  const base = API_BASE || window.location.origin
  return `${base.replace(/^http/, 'ws')}/v1/dashboard/live?access_token=${encodeURIComponent(accessToken || '')}`
}

export function healthCheck() { return request('/health') }
export function getApiV1Root() { return request('/api/v1/') }
