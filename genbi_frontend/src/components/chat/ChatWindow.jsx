import { useState } from 'react'
import { useChat } from '../../hooks/useChat'
import { QueryInput } from './QueryInput'
import { MessageBubble } from './MessageBubble'
import { SQLDisplay } from './SQLDisplay'
import { FeedbackButtons } from './FeedbackButtons'
import { DataTable } from '../data/DataTable'
import { ChartRouter } from '../visualizations/ChartRouter'
import { chatApi } from '../../services/api'

export function ChatWindow() {
  const { messages, status, sendQuestion, setFeedback } = useChat()
  const [reexecuteResults, setReexecuteResults] = useState({})

  async function handleReexecute(messageId, editedSql) {
    try {
      const result = await chatApi.executeSQL(editedSql)
      setReexecuteResults(prev => ({ ...prev, [messageId]: result }))
    } catch (_) {}
  }

  async function handleFeedback(msg, rating) {
    setFeedback(msg.id, rating)
    try {
      await chatApi.sendFeedback(msg.question, msg.sql, rating)
    } catch (_) {}
  }

  function getDisplayData(msg) {
    const override = reexecuteResults[msg.id]
    return {
      columns: override?.columns ?? msg.columns ?? [],
      rows: override?.rows ?? msg.rows ?? [],
    }
  }

  return (
    <div className="chat-window">
      {messages.map(msg => (
        msg.role === 'user' ? (
          <MessageBubble key={msg.id} role="user">
            {msg.content}
          </MessageBubble>
        ) : (
          <MessageBubble key={msg.id} role="ai">
            {msg.error ? (
              <span className="chat-error">{msg.error}</span>
            ) : (
              <>
                {msg.insight && <p className="chat-insight">{msg.insight}</p>}
                {msg.sql && (
                  <SQLDisplay
                    sql={msg.sql}
                    onReexecute={(sql) => handleReexecute(msg.id, sql)}
                  />
                )}
                <ChartRouter
                  columns={getDisplayData(msg).columns}
                  rows={getDisplayData(msg).rows}
                />
                <DataTable
                  columns={getDisplayData(msg).columns}
                  rows={getDisplayData(msg).rows}
                />
              </>
            )}
            <FeedbackButtons
              feedback={msg.feedback}
              onFeedback={(rating) => handleFeedback(msg, rating)}
            />
          </MessageBubble>
        )
      ))}

      {status === 'loading' && (
        <div data-testid="loading-indicator" className="chat-loading">
          <span className="chat-loading__dot" />
          <span>Analyse en cours…</span>
        </div>
      )}

      <QueryInput onSubmit={sendQuestion} disabled={status === 'loading'} />
    </div>
  )
}
