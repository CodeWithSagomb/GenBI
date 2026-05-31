import { useState } from 'react'
import { useChat } from '../../hooks/useChat'
import { QueryInput } from './QueryInput'
import { MessageBubble } from './MessageBubble'
import { SQLDisplay } from './SQLDisplay'
import { DataTable } from '../data/DataTable'
import { ChartRouter } from '../visualizations/ChartRouter'
import { chatApi } from '../../services/api'

export function ChatWindow() {
  const {
    status, question, sql, columns, rows, insight, error,
    sendQuestion,
  } = useChat()

  const [reexecuteResult, setReexecuteResult] = useState(null)

  async function handleReexecute(editedSql) {
    try {
      const result = await chatApi.executeSQL(editedSql)
      setReexecuteResult(result)
    } catch (_) {}
  }

  const displayColumns = reexecuteResult?.columns ?? columns
  const displayRows = reexecuteResult?.rows ?? rows
  const isLoading = status === 'loading'

  return (
    <div className="chat-window">
      {question && (
        <MessageBubble role="user">{question}</MessageBubble>
      )}

      {isLoading && (
        <div data-testid="loading-indicator" className="chat-loading">
          <span className="chat-loading__dot" />
          <span>Analyse en cours…</span>
        </div>
      )}

      {status === 'error' && (
        <MessageBubble role="ai">
          <span className="chat-error">{error}</span>
        </MessageBubble>
      )}

      {status === 'success' && (
        <MessageBubble role="ai">
          {insight && <p className="chat-insight">{insight}</p>}
          <SQLDisplay sql={sql} onReexecute={handleReexecute} />
          <ChartRouter columns={displayColumns} rows={displayRows} />
          <DataTable columns={displayColumns} rows={displayRows} />
        </MessageBubble>
      )}

      <QueryInput onSubmit={sendQuestion} disabled={isLoading} />
    </div>
  )
}
