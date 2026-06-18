import { PieChart, Pie, Cell, Tooltip, Legend, ResponsiveContainer } from 'recharts'

const COLORS = ['var(--secondary)', 'var(--primary)']

const BOOL_LABELS = { true: 'Génériques', false: 'Princeps', 1: 'Génériques', 0: 'Princeps' }

function toLabel(v) {
  if (v === null || v === undefined) return '—'
  if (v in BOOL_LABELS) return BOOL_LABELS[v]
  const s = String(v)
  return s.charAt(0).toUpperCase() + s.slice(1).replace(/_/g, ' ')
}

function buildPieData(rows) {
  if (!rows) return []
  return rows.map(row => ({ label: toLabel(row[0]), value: Number(row[1]) }))
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
