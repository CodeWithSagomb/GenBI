import { useTranslation } from 'react-i18next'
import { LineChart, Line, ResponsiveContainer } from 'recharts'

function formatNumber(val) {
  if (val === null || val === undefined) return '—'
  const num = Number(val)
  if (isNaN(num)) return String(val)
  return new Intl.NumberFormat('fr-FR').format(Math.round(num))
}

export function KPICard({ title, value, unit = '', icon: Icon, color = 'primary', loading, error, sparklineData }) {
  const { t } = useTranslation()
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
        {!loading && error && <span className="kpi-card__error">{t('dashboard.kpi_error')}</span>}
        {!loading && !error && (
          <span className="kpi-card__value">
            {formatNumber(value)}
            {unit && <span className="kpi-card__unit"> {unit}</span>}
          </span>
        )}
      </div>
      {!loading && !error && sparklineData && sparklineData.length > 1 && (
        <div className="kpi-sparkline">
          <ResponsiveContainer width="100%" height={44}>
            <LineChart data={sparklineData} margin={{ top: 4, right: 0, left: 0, bottom: 0 }}>
              <Line
                type="monotone"
                dataKey="v"
                stroke={`var(--${color === 'primary' ? 'primary' : color === 'danger' ? 'danger' : color === 'warning' ? 'warning' : color === 'ok' ? 'accent-green' : 'secondary'})`}
                strokeWidth={1.5}
                dot={false}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      )}
    </div>
  )
}
