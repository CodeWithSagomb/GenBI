import { useState, useCallback } from 'react'
import { chatApi } from '../services/api'

const INITIAL_STATE = {
  status: 'idle',   // idle | loading | success | error
  question: '',
  sql: null,
  columns: [],
  rows: [],
  row_count: 0,
  insight: null,
  error: null,
}

export function useChat() {
  const [state, setState] = useState(INITIAL_STATE)

  const sendQuestion = useCallback(async (question) => {
    if (!question || !question.trim()) return

    setState({ ...INITIAL_STATE, status: 'loading', question: question.trim() })

    try {
      // Étape 1 : génération SQL
      const { sql } = await chatApi.sendQuestion(question.trim())

      // Étape 2 : exécution SQL
      const { columns, rows, row_count } = await chatApi.executeSQL(sql)

      // Étape 3 : insight (best-effort — ne bloque pas l'affichage)
      let insight = null
      try {
        const res = await chatApi.interpret(question.trim(), { columns, rows })
        insight = res.insight
      } catch (_) {}

      setState({
        status: 'success',
        question: question.trim(),
        sql,
        columns,
        rows,
        row_count,
        insight,
        error: null,
      })
    } catch (err) {
      setState((prev) => ({
        ...prev,
        status: 'error',
        error: err.message ?? 'Une erreur inattendue est survenue.',
      }))
    }
  }, [])

  const reset = useCallback(() => setState(INITIAL_STATE), [])

  return { ...state, sendQuestion, reset }
}
