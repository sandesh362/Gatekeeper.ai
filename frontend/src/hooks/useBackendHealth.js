import { useEffect, useState } from 'react'
import { healthCheck } from '../services/api.js'

export function useBackendHealth() {
  const [status, setStatus] = useState({ loading: true, ok: false, data: null, error: null })

  useEffect(() => {
    let cancelled = false

    healthCheck()
      .then((data) => {
        if (!cancelled) setStatus({ loading: false, ok: true, data, error: null })
      })
      .catch((error) => {
        if (!cancelled) setStatus({ loading: false, ok: false, data: null, error: error.message })
      })

    return () => {
      cancelled = true
    }
  }, [])

  return status
}
