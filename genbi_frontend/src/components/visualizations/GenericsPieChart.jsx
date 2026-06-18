import { PieChart, Pie, Cell, Tooltip, Legend, ResponsiveContainer } from 'recharts'

const COLORS = ['var(--secondary)', 'var(--primary)']

const LABELS = { true: 'Génériques', false: 'Princeps', 1: 'Génériques', 0: 'Princeps' }

function buildPieData(rows) {
  if (!rows) return []
  return rows.map(row => ({
    label: LABELS[row[0]] ?? (row[0] ? 'Génériques' : 'Princeps'),
    value: Number(row[1]),
  }))
}

export function GenericsPieChart({ rows }) {
  const data = buildPieData(rows)
  if (!data.length) return null

  const total = data.reduce((s, d) => s + d.value, 0)

  return (
    <div className="chart-wrapper" data-chart-type="pie">
      <ResponsiveContainer width="100%" height={280}>
        <PieChart>
          <Pie
            data={data}
            dataKey="value"
            nameKey="label"
            cx="50%"
            cy="50%"
            outerRadius={95}
            innerRadius={50}
            paddingAngle={3}
            label={({ label, value }) =>
              `${label} ${total > 0 ? ((value / total) * 100).toFixed(0) : 0}%`
            }
            labelLine={{ stroke: 'var(--text-muted)', strokeWidth: 1 }}
          >
            {data.map((_, i) => (
              <Cell key={i} fill={COLORS[i % COLORS.length]} />
            ))}
          </Pie>
          <Tooltip
            contentStyle={{ background: 'var(--panel-bg)', border: '1px solid var(--panel-border)', borderRadius: '8px' }}
            formatter={(value, name) => [value.toLocaleString('fr-FR'), name]}
          />
          <Legend
            wrapperStyle={{ fontSize: '0.82rem', color: 'var(--text-muted)', paddingTop: '0.5rem' }}
          />
        </PieChart>
      </ResponsiveContainer>
    </div>
  )
}
