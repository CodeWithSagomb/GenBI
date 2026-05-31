const BASE_URL = import.meta.env.VITE_API_URL ?? 'http://localhost:8000'
const API_KEY = import.meta.env.VITE_API_KEY ?? ''

async function request(path, options = {}) {
  const res = await fetch(`${BASE_URL}${path}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      'X-API-Key': API_KEY,
      ...options.headers,
    },
  })

  if (!res.ok) {
    let detail = `Erreur ${res.status}`
    try {
      const body = await res.json()
      detail = body.detail ?? detail
    } catch (_) {}
    throw new Error(detail)
  }

  return res.json()
}

export const chatApi = {
  sendQuestion: (question) =>
    request('/api/v1/chat', {
      method: 'POST',
      body: JSON.stringify({ question }),
    }),

  executeSQL: (sql, limit = 100, offset = 0) =>
    request('/api/v1/execute', {
      method: 'POST',
      body: JSON.stringify({ sql, limit, offset }),
    }),

  getSchema: () => request('/api/v1/schema'),

  getSuggestions: () => request('/api/v1/suggestions'),

  interpret: (question, results) =>
    request('/api/v1/interpret', {
      method: 'POST',
      body: JSON.stringify({ question, results }),
    }),

  sendFeedback: (question, sql_generated, rating, comment = null) =>
    request('/api/v1/feedback', {
      method: 'POST',
      body: JSON.stringify({ question, sql_generated, rating, comment }),
    }),
}
