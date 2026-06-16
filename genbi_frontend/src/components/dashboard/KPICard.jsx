import { TrendingUp } from 'lucide-react'

function formatNumber(val) {
  if (val === null || val === undefined) return '—'
  const num = Number(val)
  if (isNaN(num)) return String(val)
  return new Intl.NumberFormat('fr-FR').format(Math.round(num))
}

export function KPICard({ title, value, unit = '', icon: Icon, color = 'primary', loading, error }) {
  return (
    <div className={`kpi-card kpi-card--${color}`}>
      <div className="kpi-card__header">
        <span className="kpi-card__title">{title}</span>
        {Icon && <Icon size={18} className="kpi-card__icon" />}
      </div>
      <div className="kpi-card__body">
        {loading && (
          <div className="kpi-card__skeleton">
            <div className="kpi-card__skeleton-value" />
            <div className="kpi-card__skeleton-unit" />
          </div>
        )}
        {!loading && error && <span className="kpi-card__error">Erreur</span>}
        {!loading && !error && (
          <span className="kpi-card__value">
            {formatNumber(value)}
            {unit && <span className="kpi-card__unit"> {unit}</span>}
          </span>
        )}
      </div>
    </div>
  )
}
