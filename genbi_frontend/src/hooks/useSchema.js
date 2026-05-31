import { useState, useEffect } from 'react'
import { chatApi } from '../services/api'

export function useSchema() {
  const [schema, setSchema] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    chatApi.getSchema()
      .then((data) => setSchema(data.schema ?? data))
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false))
  }, [])

  return { schema, loading, error }
}
