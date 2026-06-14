import { useState } from 'react'
import { Copy, Check } from 'lucide-react'
import { useToast } from '../../hooks/useToast'

export function SQLDisplay({ sql, onReexecute, isExecuting = false, reexecuteError }) {
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
      toast?.('SQL copié dans le presse-papiers')
      setTimeout(() => setCopied(false), 2000)
    } catch (_) {}
  }

  return (
    <div data-testid="sql-display" className="sql-display">
      <div className="sql-display__header">
        <span className="sql-display__label">SQL généré</span>
        <div className="sql-display__actions">
          <button
            className="sql-display__edit-btn"
            onClick={handleCopy}
            title="Copier le SQL"
            aria-label="Copier le SQL"
          >
            {copied ? <Check size={13} /> : <Copy size={13} />}
          </button>
          {onReexecute && !editing && (
            <button className="sql-display__edit-btn" onClick={() => setEditing(true)}>
              Modifier
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
              Annuler
            </button>
            <button
              className="sql-display__run-btn"
              onClick={handleReexecute}
              disabled={isExecuting}
            >
              {isExecuting ? 'Exécution…' : 'Ré-exécuter'}
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
