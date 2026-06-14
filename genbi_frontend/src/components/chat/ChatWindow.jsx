import { useState, useRef, useEffect } from 'react'
import { Trash2 } from 'lucide-react'
import { useChat } from '../../hooks/useChat'
import { QueryInput } from './QueryInput'
import { MessageBubble } from './MessageBubble'
import { SQLDisplay } from './SQLDisplay'
import { FeedbackButtons } from './FeedbackButtons'
import { DataTable } from '../data/DataTable'
import { ChartRouter } from '../visualizations/ChartRouter'
import { chatApi } from '../../services/api'

export function ChatWindow() {
  const { messages, status, sendQuestion, setFeedback, clearChat: clearChatState } = useChat()
  const [reexecuteResults, setReexecuteResults] = useState({})
  const [reexecuteLoading, setReexecuteLoading] = useState({})
  const [reexecuteErrors, setReexecuteErrors] = useState({})
  const bottomRef = useRef(null)

  function clearChat() {
    clearChatState()
    setReexecuteResults({})
    setReexecuteLoading({})
    setReexecuteErrors({})
  }

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  async function handleReexecute(messageId, editedSql) {
    setReexecuteLoading(prev => ({ ...prev, [messageId]: true }))
    setReexecuteErrors(prev => { const n = { ...prev }; delete n[messageId]; return n })
    try {
      const result = await chatApi.executeSQL(editedSql)
      setReexecuteResults(prev => ({ ...prev, [messageId]: result }))
    } catch (err) {
      setReexecuteErrors(prev => ({ ...prev, [messageId]: err.message ?? 'Erreur d\'exécution SQL.' }))
    } finally {
      setReexecuteLoading(prev => { const n = { ...prev }; delete n[messageId]; return n })
    }
  }

  async function handleFeedback(msg, rating) {
    const sub = msg.sub_analyses?.[0]
    if (!sub) return
    setFeedback(msg.id, rating)
    try {
      await chatApi.sendFeedback(msg.question, sub.sql, rating)
    } catch (_) {}
  }

  function getSimpleDisplayData(msg) {
    const override = reexecuteResults[msg.id]
    const sub = msg.sub_analyses?.[0] ?? {}
    return {
      columns: override?.columns ?? sub.columns ?? [],
      rows: override?.rows ?? sub.rows ?? [],
      rowCount: override?.row_count ?? sub.row_count ?? null,
    }
  }

  function renderSimpleMessage(msg) {
    const sub = msg.sub_analyses?.[0] ?? {}
    const display = getSimpleDisplayData(msg)
    return (
      <>
        {sub.insight && <p className="chat-insight">{sub.insight}</p>}
        {sub.sql && (
          <SQLDisplay
            sql={sub.sql}
            onReexecute={(sql) => handleReexecute(msg.id, sql)}
            isExecuting={!!reexecuteLoading[msg.id]}
            reexecuteError={reexecuteErrors[msg.id]}
          />
        )}
        <ChartRouter columns={display.columns} rows={display.rows} />
        <DataTable
          columns={display.columns}
          rows={display.rows}
          rowCount={display.rowCount}
        />
        <FeedbackButtons
          feedback={msg.feedback}
          onFeedback={(rating) => handleFeedback(msg, rating)}
        />
      </>
    )
  }

  function renderCompoundMessage(msg) {
    return (
      <>
        {msg.sub_analyses.map((sub, i) => (
          <div key={i} className="sub-analysis">
            <p className="sub-analysis__title">{sub.question}</p>
            {sub.insight && <p className="chat-insight">{sub.insight}</p>}
            {sub.columns?.length > 0 && (
              <DataTable
                columns={sub.columns}
                rows={sub.rows}
                rowCount={sub.row_count}
              />
            )}
          </div>
        ))}
      </>
    )
  }

  return (
    <div className="chat-window">
      {messages.length > 0 && (
        <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
          <button
            className="sql-display__edit-btn"
            onClick={clearChat}
            title="Effacer la conversation"
          >
            <Trash2 size={14} />
          </button>
        </div>
      )}
      {messages.map(msg => (
        msg.role === 'user' ? (
          <MessageBubble key={msg.id} role="user">
            {msg.content}
          </MessageBubble>
        ) : (
          <MessageBubble key={msg.id} role="ai">
            {msg.error ? (
              <span className="chat-error">{msg.error}</span>
            ) : msg.is_compound ? (
              renderCompoundMessage(msg)
            ) : (
              renderSimpleMessage(msg)
            )}
          </MessageBubble>
        )
      ))}

      {status === 'loading' && (
        <div data-testid="loading-indicator" className="chat-loading">
          <span className="chat-loading__dot" />
          <span>Analyse en cours…</span>
        </div>
      )}

      <div ref={bottomRef} />
      <QueryInput onSubmit={sendQuestion} disabled={status === 'loading'} />
    </div>
  )
}
