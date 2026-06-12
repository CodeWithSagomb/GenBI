import { useState, useRef, useCallback } from 'react'
import { chatApi } from '../services/api'

export function useChat() {
  const [messages, setMessages] = useState([])
  const [status, setStatus] = useState('idle')
  const nextId = useRef(0)

  const sendQuestion = useCallback(async (question) => {
    if (!question?.trim()) return

    const q = question.trim()
    const userId = nextId.current++
    const aiId = nextId.current++

    setMessages(prev => [...prev, { id: userId, role: 'user', content: q }])
    setStatus('loading')

    try {
      const result = await chatApi.analyse(q)

      setMessages(prev => [...prev, {
        id: aiId,
        role: 'ai',
        question: q,
        is_compound: result.is_compound,
        sub_analyses: result.sub_analyses,
        error: null,
        feedback: null,
      }])
    } catch (err) {
      setMessages(prev => [...prev, {
        id: aiId,
        role: 'ai',
        error: err.message ?? 'Une erreur inattendue est survenue.',
        feedback: null,
      }])
    } finally {
      setStatus('idle')
    }
  }, [])

  const setFeedback = useCallback((messageId, rating) => {
    setMessages(prev =>
      prev.map(msg => msg.id === messageId ? { ...msg, feedback: rating } : msg)
    )
  }, [])

  return { messages, status, sendQuestion, setFeedback }
}
