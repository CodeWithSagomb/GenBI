import { useState, useEffect, useCallback } from 'react'
import { chatApi } from '../services/api'

export function useAlerts() {
  const [alerts, setAlerts] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  const fetch = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const res = await chatApi.getAlerts()
      setAlerts(res.alerts ?? [])
    } catch (e) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => { fetch() }, [fetch])

  return { alerts, loading, error, refetch: fetch }
}
