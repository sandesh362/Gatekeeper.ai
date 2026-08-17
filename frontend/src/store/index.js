import { create } from 'zustand'

export const useAppStore = create((set) => ({
  sidebarOpen: true,
  connectionStatus: 'disconnected',
  liveFeed: [],
  logFilters: { decision: '', provider: '', start: '', end: '' },
  toggleSidebar: () => set((state) => ({ sidebarOpen: !state.sidebarOpen })),
  setConnectionStatus: (connectionStatus) => set({ connectionStatus }),
  addLiveEvent: (event) => set((state) => ({ liveFeed: [event, ...state.liveFeed].slice(0, 50) })),
  setLogFilters: (filters) => set({ logFilters: filters }),
}))
