import { useTranslation } from 'react-i18next'

function formatHeader(col) {
  return col.split('_').map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(' ')
}

function formatCell(val) {
  if (val === null || val === undefined) return '—'
  const num = Number(val)
  if (!isNaN(num) && String(val).trim() !== '') {
    return new Intl.NumberFormat('fr-FR').format(Math.round(num * 100) / 100)
  }
  return String(val)
}

export function AlertTable({ title, columns, rows, loading, error, severity = 'warning' }) {
  const { t } = useTranslation()
  return (
    <div className={`alert-card alert-card--${severity}`}>
      <div className="alert-card__header">
        <span className="alert-card__dot" />
        <span className="alert-card__title">{title}</span>
        {!loading && !error && rows && (
          <span className="alert-card__badge">{rows.length}</span>
        )}
      </div>

      <div className="alert-card__body">
        {loading && <p className="alert-card__state">{t('dashboard.alert_loading')}</p>}
        {error   && <p className="alert-card__state alert-card__state--error">{t('dashboard.alert_error')}</p>}
        {!loading && !error && (!rows || rows.length === 0) && (
          <p className="alert-card__state alert-card__state--ok">{t('dashboard.alert_ok')}</p>
        )}
        {!loading && !error && rows && rows.length > 0 && (
          <div className="alert-table__wrapper">
            <table className="alert-table">
              <thead>
                <tr>
                  {columns.map(col => (
                    <th key={col} className="alert-table__th">{formatHeader(col)}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {rows.map((row, i) => (
                  <tr key={i} className="alert-table__row">
                    {row.map((cell, j) => (
                      <td key={j} className="alert-table__td">{formatCell(cell)}</td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  )
}
