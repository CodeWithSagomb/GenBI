import { useState } from 'react'
import { Copy, Check } from 'lucide-react'
import { useTranslation } from 'react-i18next'
import { useToast } from '../../hooks/useToast'

export function SQLDisplay({ sql, onReexecute, isExecuting = false, reexecuteError }) {
  const { t } = useTranslation()
  const [editing, setEditing] = useState(false)
  const [editedSql, setEditedSql] = useState(sql ?? '')
  const [copied, setCopied] = useState(false)
  const toast = useToast()

  if (!sql) return null

  function handleReexecute() {
    setEditing(false)
    onReexecute?.(editedSql)
  }

  async function handleCopy() {
    try {
      await navigator.clipboard.writeText(sql)
      setCopied(true)
      toast?.(t('chat.sql_copied'))
      setTimeout(() => setCopied(false), 2000)
    } catch (_) {}
  }

  return (
    <div data-testid="sql-display" className="sql-display">
      <div className="sql-display__header">
        <span className="sql-display__label">{t('chat.sql_label')}</span>
        <div className="sql-display__actions">
          <button
            className="sql-display__edit-btn"
            onClick={handleCopy}
            title={t('chat.sql_copy_title')}
            aria-label={t('chat.sql_copy_title')}
          >
            {copied ? <Check size={13} /> : <Copy size={13} />}
          </button>
          {onReexecute && !editing && (
            <button className="sql-display__edit-btn" onClick={() => setEditing(true)}>
              {t('chat.sql_edit')}
            </button>
          )}
        </div>
      </div>

      {editing ? (
        <div className="sql-display__editor">
          <textarea
            className="sql-display__textarea"
            value={editedSql}
            onChange={(e) => setEditedSql(e.target.value)}
            rows={5}
          />
          <div className="sql-display__editor-actions">
            <button className="sql-display__cancel-btn" onClick={() => setEditing(false)}>
              {t('chat.sql_cancel')}
            </button>
            <button
              className="sql-display__run-btn"
              onClick={handleReexecute}
              disabled={isExecuting}
            >
              {isExecuting ? t('chat.sql_executing') : t('chat.sql_rerun')}
            </button>
          </div>
          {reexecuteError && (
            <p className="sql-display__error">{reexecuteError}</p>
          )}
        </div>
      ) : (
        <pre className="sql-display__code">
          <code role="code">{sql}</code>
        </pre>
      )}
    </div>
  )
}
