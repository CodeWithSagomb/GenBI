import { useState, useRef, useCallback, useEffect } from 'react'
import i18n from '../i18n/index'
import { chatApi } from '../services/api'

function _buildHistory(msgs) {
  return msgs
    .filter(m => m.role === 'ai' && !m.error && m.sub_analyses?.[0]?.sql)
    .slice(-3)
    .flatMap(m => [
      { role: 'user', content: m.question },
      { role: 'assistant', content: m.sub_analyses[0].sql },
    ])
}

export function useChat() {
  const [messages, setMessages] = useState([])
  const [status, setStatus] = useState('idle')
  const nextId = useRef(0)
  // Buffer de tokens : découple réseau (rapide) du rendu React (50ms interval)
  const tokenBuf = useRef('')
  const streamingId = useRef(null)
  const intervalRef = useRef(null)

  // Flush le buffer vers le state toutes les 50ms
  useEffect(() => {
    intervalRef.current = setInterval(() => {
      if (streamingId.current === null || tokenBuf.current === '') return
      const chunk = tokenBuf.current
      tokenBuf.current = ''
      const targetId = streamingId.current
      setMessages(prev => prev.map(m =>
        m.id === targetId
          ? { ...m, sub_analyses: m.sub_analyses.map((s, i) =>
              i === 0 ? { ...s, insight: s.insight + chunk } : s) }
          : m
      ))
    }, 50)
    return () => clearInterval(intervalRef.current)
  }, [])

  const sendQuestion = useCallback(async (question) => {
    if (!question?.trim()) return

    const q = question.trim()
    const userId = nextId.current++
    const aiId = nextId.current++
    const history = _buildHistory(messages)
    const enWords = /\b(what|how|which|who|when|where|show|give|list|total|best|top|my|by|per|of|the|is|are|do|does|did|have|has)\b/i
    const frWords = /\b(quel|quelle|quels|quelles|comment|combien|quoi|qui|quand|où|montre|donne|liste|mon|ma|mes|par|de|le|la|les|est|sont|ont|fait|avez|j'ai)\b/i
    const enScore = (q.match(enWords) || []).length
    const frScore = (q.match(frWords) || []).length
    const language = enScore > frScore ? 'en' : (i18n.language || 'fr')

    setMessages(prev => [...prev, { id: userId, role: 'user', content: q }])
    setStatus('loading')

    try {
      let dataReceived = false
      for await (const event of chatApi.analyseStream(q, history, language)) {
        if (event.type === 'compound') {
          const result = event.result
          setMessages(prev => [...prev, {
            id: aiId, role: 'ai', question: q,
            is_compound: result.is_compound, sub_analyses: result.sub_analyses,
            error: null, feedback: null, timestamp: Date.now(),
          }])
          dataReceived = true
          break
        }

        if (event.type === 'data') {
          // Affiche la table immédiatement — l'insight sera streame ensuite via le buffer
          tokenBuf.current = ''
          streamingId.current = aiId
          setMessages(prev => [...prev, {
            id: aiId, role: 'ai', question: q,
            is_compound: false,
            sub_analyses: [{
              question: q, sql: event.sql, columns: event.columns,
              rows: event.rows, row_count: event.row_count,
              insight: '', viz_hint: event.viz_hint,
            }],
            error: null, feedback: null, timestamp: Date.now(),
          }])
          setStatus('streaming')
          dataReceived = true
        }

        if (event.type === 'token') {
          // Accumule dans le buffer — le interval flush vers React toutes les 50ms
          tokenBuf.current += event.content
        }

        if (event.type === 'done') {
          // Flush le buffer restant, puis remplace par la version post-processée
          streamingId.current = null
          const remaining = tokenBuf.current
          tokenBuf.current = ''
          setMessages(prev => prev.map(m =>
            m.id === aiId
              ? { ...m, sub_analyses: m.sub_analyses.map((s, i) =>
                  i === 0 ? { ...s, insight: event.insight } : s) }
              : m
          ))
          void remaining  // le buffer est ignoré — done contient l'insight complet corrigé
        }

        if (event.type === 'error') throw new Error(event.message)
      }
      if (!dataReceived) throw new Error(i18n.t('chat.error_default'))
    } catch (err) {
      streamingId.current = null
      tokenBuf.current = ''
      setMessages(prev => {
        const existing = prev.find(m => m.id === aiId)
        if (existing) return prev
        return [...prev, {
          id: aiId, role: 'ai',
          error: err.message ?? i18n.t('chat.error_default'),
          feedback: null,
        }]
      })
    } finally {
      streamingId.current = null
      setStatus('idle')
    }
  }, [messages])

  const setFeedback = useCallback((messageId, rating) => {
    setMessages(prev =>
      prev.map(msg => msg.id === messageId ? { ...msg, feedback: rating } : msg)
    )
  }, [])

  const clearChat = useCallback(() => {
    setMessages([])
    nextId.current = 0
  }, [])

  return { messages, status, sendQuestion, setFeedback, clearChat }
}
