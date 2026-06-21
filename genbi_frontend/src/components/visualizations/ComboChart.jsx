import {
  ComposedChart, Line, Bar, XAxis, YAxis, CartesianGrid,
  Tooltip, Legend, ResponsiveContainer,
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

function formatHeader(col) {
  return col.split('_').map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(' ')
}

function formatY(v) {
  if (v >= 1_000_000) return `${(v / 1_000_000).toFixed(1)}M`
  if (v >= 1_000) return `${(v / 1_000).toFixed(0)}k`
  return v
}

export function ComboChart({ data, xKey, barKey, lineKey, months = FR_MONTHS_DEFAULT }) {
  const formatTick = makeFormatTick(months)
  return (
    <div className="chart-wrapper" data-chart-type="combo">
      <ResponsiveContainer width="100%" height={280}>
        <ComposedChart data={data} margin={{ top: 8, right: 24, left: 0, bottom: 8 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="var(--panel-border)" />
          <XAxis
            dataKey={xKey}
            tick={{ fill: 'var(--text-muted)', fontSize: 12 }}
            tickFormatter={formatTick}
          />
          <YAxis
            yAxisId="bar"
            orientation="left"
            tick={{ fill: 'var(--text-muted)', fontSize: 11 }}
            tickFormatter={formatY}
          />
          <YAxis
            yAxisId="line"
            orientation="right"
            tick={{ fill: 'var(--text-muted)', fontSize: 11 }}
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
          <Legend wrapperStyle={{ fontSize: '0.8rem', color: 'var(--text-muted)' }} />
          <Bar
            yAxisId="bar"
            dataKey={barKey}
            name={formatHeader(barKey)}
            fill="var(--primary)"
            radius={[4, 4, 0, 0]}
            opacity={0.75}
          />
          <Line
            yAxisId="line"
            type="monotone"
            dataKey={lineKey}
            name={formatHeader(lineKey)}
            stroke="var(--secondary)"
            strokeWidth={2}
            dot={{ r: 3 }}
            activeDot={{ r: 5 }}
          />
        </ComposedChart>
      </ResponsiveContainer>
    </div>
  )
}
