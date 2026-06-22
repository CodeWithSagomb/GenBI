import { useState, useRef, useCallback } from 'react'
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

  const sendQuestion = useCallback(async (question) => {
    if (!question?.trim()) return

    const q = question.trim()
    const userId = nextId.current++
    const aiId = nextId.current++
    const history = _buildHistory(messages)
    // Auto-detect: if question is mostly English words, override UI language
    const enWords = /\b(what|how|which|who|when|where|show|give|list|total|best|top|my|by|per|of|the|is|are|do|does|did|have|has)\b/i
    const frWords = /\b(quel|quelle|quels|quelles|comment|combien|quoi|qui|quand|où|montre|donne|liste|mon|ma|mes|par|de|le|la|les|est|sont|ont|fait|avez|j'ai)\b/i
    const enScore = (q.match(enWords) || []).length
    const frScore = (q.match(frWords) || []).length
    const language = enScore > frScore ? 'en' : (i18n.language || 'fr')

    setMessages(prev => [...prev, { id: userId, role: 'user', content: q }])
    setStatus('loading')

    try {
      const result = await chatApi.analyse(q, history, language)
      setMessages(prev => [...prev, {
        id: aiId,
        role: 'ai',
        question: q,
        is_compound: result.is_compound,
        sub_analyses: result.sub_analyses,
        error: null,
        feedback: null,
        timestamp: Date.now(),
      }])
    } catch (err) {
      setMessages(prev => [...prev, {
        id: aiId,
        role: 'ai',
        error: err.message ?? i18n.t('chat.error_default'),
        feedback: null,
      }])
    } finally {
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
