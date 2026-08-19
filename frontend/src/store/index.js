import { create } from 'zustand'

export const useAppStore = create((set) => ({
  sidebarOpen: true,
  connectionStatus: 'disconnected',
  liveFeed: [],
  logFilters: { decision: '', provider: '', start: '', end: '' },
  accessToken: null,
  authReady: false,
  toggleSidebar: () => set((state) => ({ sidebarOpen: !state.sidebarOpen })),
  setConnectionStatus: (connectionStatus) => set({ connectionStatus }),
  addLiveEvent: (event) => set((state) => ({ liveFeed: [event, ...state.liveFeed].slice(0, 50) })),
  setLogFilters: (filters) => set({ logFilters: filters }),
  setAccessToken: (accessToken) => set({ accessToken, authReady: true }),
  clearSession: () => set({ accessToken: null, authReady: true }),
}))
