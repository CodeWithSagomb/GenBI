import { useState } from 'react'

export function SQLDisplay({ sql, onReexecute }) {
  const [editing, setEditing] = useState(false)
  const [editedSql, setEditedSql] = useState(sql ?? '')

  if (!sql) return null

  function handleReexecute() {
    setEditing(false)
    onReexecute?.(editedSql)
  }

  return (
    <div data-testid="sql-display" className="sql-display">
      <div className="sql-display__header">
        <span className="sql-display__label">SQL généré</span>
        {onReexecute && !editing && (
          <button className="sql-display__edit-btn" onClick={() => setEditing(true)}>
            Modifier
          </button>
        )}
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
            <button className="sql-display__run-btn" onClick={handleReexecute}>
              Ré-exécuter
            </button>
          </div>
        </div>
      ) : (
        <pre className="sql-display__code">
          <code role="code">{sql}</code>
        </pre>
      )}
    </div>
  )
}
