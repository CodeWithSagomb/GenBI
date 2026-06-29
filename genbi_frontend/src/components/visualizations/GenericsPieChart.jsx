import { PieChart, Pie, Cell, Tooltip, Legend, ResponsiveContainer, Label } from 'recharts'

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

function toLabel(v) {
  if (v === null || v === undefined) return '—'
  const s = String(v)
  return s.charAt(0).toUpperCase() + s.slice(1).replace(/_/g, ' ')
}

function buildPieData(rows) {
  if (!rows) return []
  return rows.map(row => ({ label: toLabel(row[0]), value: Number(row[1]) }))
}

function formatTotal(total) {
  if (total >= 1_000_000) return `${(total / 1_000_000).toFixed(1)}M`
  if (total >= 1_000) return `${(total / 1_000).toFixed(0)}k`
  return total.toLocaleString('fr-FR')
}

function CenterLabel({ viewBox, total }) {
  const { cx, cy } = viewBox ?? {}
  if (!cx || !cy) return null
  return (
    <text x={cx} y={cy} textAnchor="middle" dominantBaseline="middle" fill="var(--text)" fontSize={14} fontWeight="600">
      {formatTotal(total)}
    </text>
  )
}

export function GenericsPieChart({ rows }) {
  const data = buildPieData(rows)
  if (!data.length) return null

  const total = data.reduce((sum, d) => sum + d.value, 0)

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
            label={({ percent }) => percent >= 0.05 ? `${Math.round(percent * 100)}%` : ''}
            labelLine={false}
          >
            <Label content={(props) => <CenterLabel {...props} total={total} />} />
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
