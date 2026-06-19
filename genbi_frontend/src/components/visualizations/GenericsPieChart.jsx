import { PieChart, Pie, Cell, Tooltip, Legend, ResponsiveContainer } from 'recharts'

const COLORS = [
  'var(--secondary)',           // cyan
  'var(--primary)',             // violet
  'var(--accent-green)',        // vert
  'var(--warning)',             // orange
  'var(--danger)',              // rouge
  'hsl(300, 65%, 58%)',        // magenta
  'hsl(55, 90%, 55%)',         // jaune
  'hsl(170, 70%, 45%)',        // teal
]

// B-01: PostgreSQL sérialise les booléens en "t"/"f" dans les résultats JSON
const BOOL_LABELS = {
  true: 'Génériques', false: 'Princeps',
  1: 'Génériques', 0: 'Princeps',
  t: 'Génériques', f: 'Princeps',
}

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
            label={({ label, percent }) =>
              percent >= 0.05 ? `${label} ${Math.round(percent * 100)}%` : ''
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
