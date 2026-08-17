import { useEffect } from 'react'
import { liveDashboardUrl } from '../services/api.js'
import { useAppStore } from '../store/index.js'

export function useLiveDashboard() {
  const setConnectionStatus = useAppStore((state) => state.setConnectionStatus)
  const addLiveEvent = useAppStore((state) => state.addLiveEvent)
  useEffect(() => {
    let retry; let socket
    const connect = () => {
      setConnectionStatus('connecting'); socket = new WebSocket(liveDashboardUrl())
      socket.onopen = () => setConnectionStatus('connected')
      socket.onmessage = (event) => addLiveEvent(JSON.parse(event.data))
      socket.onerror = () => socket.close()
      socket.onclose = () => { setConnectionStatus('disconnected'); retry = window.setTimeout(connect, 3000) }
    }
    connect(); return () => { window.clearTimeout(retry); socket?.close() }
  }, [addLiveEvent, setConnectionStatus])
}
