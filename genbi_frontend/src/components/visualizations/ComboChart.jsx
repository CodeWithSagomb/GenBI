import {
  ComposedChart, Line, Bar, XAxis, YAxis, CartesianGrid,
  Tooltip, Legend, ResponsiveContainer,
} from 'recharts'

const FR_MONTHS = ['Jan','Fév','Mar','Avr','Mai','Juin','Juil','Aoû','Sep','Oct','Nov','Déc']

function formatTick(value) {
  if (typeof value === 'string' && /^\d{4}-\d{2}/.test(value)) {
    const d = new Date(value)
    if (!isNaN(d)) return `${FR_MONTHS[d.getUTCMonth()]} ${d.getUTCFullYear()}`
  }
  return value
}

function formatHeader(col) {
  return col.split('_').map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(' ')
}

export function ComboChart({ data, xKey, barKey, lineKey }) {
  return (
    <div className="chart-wrapper" data-chart-type="combo">
      <ResponsiveContainer width="100%" height={280}>
        <ComposedChart data={data} margin={{ top: 8, right: 24, left: 0, bottom: 8 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.08)" />
          <XAxis
            dataKey={xKey}
            tick={{ fill: 'var(--text-muted)', fontSize: 12 }}
            tickFormatter={formatTick}
          />
          <YAxis
            yAxisId="bar"
            orientation="left"
            tick={{ fill: 'var(--text-muted)', fontSize: 11 }}
          />
          <YAxis
            yAxisId="line"
            orientation="right"
            tick={{ fill: 'var(--text-muted)', fontSize: 11 }}
          />
          <Tooltip
            contentStyle={{ background: 'var(--panel-bg)', border: '1px solid var(--panel-border)', borderRadius: '8px' }}
            labelFormatter={formatTick}
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
