import { useState, useRef, useEffect } from 'react'
import { Trash2 } from 'lucide-react'
import { useTranslation } from 'react-i18next'
import { useChat } from '../../hooks/useChat'
import { QueryInput } from './QueryInput'
import { MessageBubble } from './MessageBubble'
import { SQLDisplay } from './SQLDisplay'
import { FeedbackButtons } from './FeedbackButtons'
import { DataTable } from '../data/DataTable'
import { ChartRouter } from '../visualizations/ChartRouter'
import { chatApi } from '../../services/api'

export function ChatWindow() {
  const { t } = useTranslation()
  const { messages, status, sendQuestion, setFeedback, clearChat: clearChatState } = useChat()
  const [reexecuteResults, setReexecuteResults] = useState({})
  const [reexecuteLoading, setReexecuteLoading] = useState({})
  const [reexecuteErrors, setReexecuteErrors] = useState({})
  const bottomRef = useRef(null)

  function formatTime(ts) {
    if (!ts) return ''
    const mins = Math.floor((Date.now() - ts) / 60000)
    if (mins < 1) return t('chat.time_now')
    if (mins < 60) return t('chat.time_ago', { mins })
    return new Date(ts).toLocaleTimeString(t('app.logo') === 'RuwaGenBI' ? 'fr-FR' : 'en-GB', { hour: '2-digit', minute: '2-digit' })
  }

  function getConfidence(rows) {
    if (!rows || rows.length === 0) return { level: 'empty', label: t('chat.confidence_no_data') }
    if (rows.length >= 10) return { level: 'high', label: t('chat.confidence_results_other', { count: rows.length }) }
    if (rows.length >= 2)  return { level: 'medium', label: t('chat.confidence_results_other', { count: rows.length }) }
    return { level: 'low', label: t('chat.confidence_results_one') }
  }

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
      setReexecuteErrors(prev => ({ ...prev, [messageId]: err.message ?? t('chat.sql_error') }))
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
    const conf = getConfidence(display.rows)
    return (
      <>
        {sub.insight && <p className="chat-insight">{sub.insight}</p>}
        <div className={`confidence-badge confidence-badge--${conf.level}`}>
          <span className={`confidence-dot confidence-dot--${conf.level}`} />
          {conf.label}
        </div>
        {sub.sql && (
          <SQLDisplay
            sql={sub.sql}
            onReexecute={(sql) => handleReexecute(msg.id, sql)}
            isExecuting={!!reexecuteLoading[msg.id]}
            reexecuteError={reexecuteErrors[msg.id]}
          />
        )}
        <ChartRouter columns={display.columns} rows={display.rows} vizHint={reexecuteResults[msg.id] ? null : (sub.viz_hint ?? null)} />
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
      <div className="compound-timeline">
        {msg.sub_analyses.map((sub, i) => (
          <div key={i} className="compound-step">
            <div className="compound-step__indicator">
              <div className="compound-step__number">{i + 1}</div>
              {i < msg.sub_analyses.length - 1 && (
                <div className="compound-step__connector" />
              )}
            </div>
            <div className="compound-step__content">
              <p className="compound-step__question">{sub.question}</p>
              {sub.insight && <p className="chat-insight">{sub.insight}</p>}
              {sub.columns?.length > 0 && (
                <>
                  <ChartRouter columns={sub.columns} rows={sub.rows} vizHint={sub.viz_hint ?? null} />
                  <DataTable
                    columns={sub.columns}
                    rows={sub.rows}
                    rowCount={sub.row_count}
                  />
                </>
              )}
            </div>
          </div>
        ))}
      </div>
    )
  }

  return (
    <div className="chat-window">
      {messages.length > 0 && (
        <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
          <button
            className="sql-display__edit-btn"
            onClick={clearChat}
            title={t('chat.clear_title')}
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
            {msg.timestamp && (
              <span className="message-timestamp">{formatTime(msg.timestamp)}</span>
            )}
          </MessageBubble>
        )
      ))}

      {status === 'loading' && (
        <div data-testid="loading-indicator" className="chat-loading">
          <span className="chat-loading__dot" />
          <span className="chat-loading__dot" />
          <span className="chat-loading__dot" />
          <span>{t('chat.analyzing')}</span>
        </div>
      )}

      <div ref={bottomRef} />
      <QueryInput onSubmit={sendQuestion} disabled={status === 'loading'} />
    </div>
  )
}
