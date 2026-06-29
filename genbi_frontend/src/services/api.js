import i18n from '../i18n/index'

const BASE_URL = import.meta.env.VITE_API_URL ?? 'http://localhost:8000'

function _authHeaders() {
  const token = typeof localStorage !== 'undefined' ? localStorage.getItem('genbi_token') : null
  return token ? { Authorization: `Bearer ${token}` } : {}
}

async function request(path, options = {}) {
  const res = await fetch(`${BASE_URL}${path}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ..._authHeaders(),
      ...options.headers,
    },
  })

  if (res.status === 401) {
    if (typeof localStorage !== 'undefined') localStorage.removeItem('genbi_token')
    throw new Error(i18n.t('errors.session_expired'))
  }

  if (!res.ok) {
    let detail = i18n.t('errors.http_error', { status: res.status })
    try {
      const body = await res.json()
      if (Array.isArray(body.detail)) {
        // Pydantic validation error → [{msg: "Value error, ..."}]
        const raw = body.detail[0]?.msg?.replace(/^Value error,\s*/i, '') ?? detail
        detail = raw === 'SQL_INJECTION'
          ? i18n.t('errors.sql_injection')
          : raw
      } else {
        detail = body.error ?? body.detail ?? detail
      }
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

  analyse: (question, conversationHistory = [], language = 'fr') =>
    request('/api/v1/analyse', {
      method: 'POST',
      body: JSON.stringify({ question, conversation_history: conversationHistory, language }),
    }),

  // Streaming SSE : async generator qui yield des événements {type, ...}
  async *analyseStream(question, conversationHistory = [], language = 'fr') {
    const res = await fetch(`${BASE_URL}/api/v1/analyse/stream`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ..._authHeaders(),
      },
      body: JSON.stringify({ question, conversation_history: conversationHistory, language }),
    })
    if (res.status === 401) {
      if (typeof localStorage !== 'undefined') localStorage.removeItem('genbi_token')
      throw new Error(i18n.t('errors.session_expired'))
    }
    if (!res.ok) throw new Error(i18n.t('errors.http_error', { status: res.status }))

    const reader = res.body.getReader()
    const decoder = new TextDecoder()
    let buf = ''
    while (true) {
      const { done, value } = await reader.read()
      if (done) break
      buf += decoder.decode(value, { stream: true })
      const lines = buf.split('\n')
      buf = lines.pop() ?? ''
      for (const line of lines) {
        if (line.startsWith('data: ')) {
          try {
            yield JSON.parse(line.slice(6))
            // Un microtask entre chaque event — évite que React batchifie tous les tokens
            await new Promise(r => setTimeout(r, 0))
          } catch (_) {}
        }
      }
    }
  },

  getAlerts: () => request('/api/v1/alerts'),
}

export const authApi = {
  login: (email, password) =>
    request('/api/v1/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    }),

  me: () => request('/api/v1/auth/me'),
}
