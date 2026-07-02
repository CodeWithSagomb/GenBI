import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
} from 'recharts'

const FR_MONTHS_DEFAULT = ['Jan','Fév','Mar','Avr','Mai','Juin','Juil','Aoû','Sep','Oct','Nov','Déc']

function makeFormatTick(months) {
  return function formatTick(value) {
    if (typeof value === 'string' && /^\d{4}-\d{2}/.test(value)) {
      const d = new Date(value)
      if (!isNaN(d)) return `${months[d.getUTCMonth()]} ${d.getUTCFullYear()}`
    }
    if (typeof value === 'number' && value >= 1 && value <= 12) return months[value - 1]
    return value
  }
}

function formatY(v) {
  if (v >= 1_000_000) return `${(v / 1_000_000).toFixed(1)}M`
  if (v >= 1_000) return `${(v / 1_000).toFixed(0)}k`
  return v
}

export function SalesLineChart({ data, xKey, yKey, months = FR_MONTHS_DEFAULT }) {
  const formatTick = makeFormatTick(months)
  return (
    <div className="chart-wrapper" data-chart-type="line">
      <ResponsiveContainer width="100%" height={280}>
        <LineChart data={data} margin={{ top: 8, right: 24, left: 0, bottom: 8 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="var(--panel-border)" />
          <XAxis
            dataKey={xKey}
            tick={{ fill: 'var(--text-muted)', fontSize: 12 }}
            tickFormatter={formatTick}
            padding={{ left: 20, right: 20 }}
          />
          <YAxis
            tick={{ fill: 'var(--text-muted)', fontSize: 12 }}
            tickFormatter={formatY}
          />
          <Tooltip
            contentStyle={{ background: 'var(--panel-bg)', border: '1px solid var(--panel-border)', borderRadius: '8px' }}
            labelFormatter={formatTick}
            formatter={(value, name) => [
              typeof value === 'number' ? value.toLocaleString('fr-FR') : value,
              name,
            ]}
          />
          <Line
            type="monotone"
            dataKey={yKey}
            stroke="var(--secondary)"
            strokeWidth={2}
            dot={{ r: 3 }}
            activeDot={{ r: 5 }}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  )
}
