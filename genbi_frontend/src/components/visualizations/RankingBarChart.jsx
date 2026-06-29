import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell,
} from 'recharts'

const COLORS = [
  'var(--primary)',
  'var(--secondary)',
  'var(--accent-green)',
  'var(--warning)',
  'var(--danger)',
  'hsl(300, 65%, 58%)',
  'hsl(55, 90%, 55%)',
  'hsl(170, 70%, 45%)',
]

// Custom tick rendu hors du clipPath SVG de recharts — évite le problème
// de l'espace disparaissant quand un caractère accentué (é, è…) tombe
// exactement à la frontière du clip (ex: "OméprazoleBiogaran" → espace perdu).
function YTick({ x, y, payload, maxChars }) {
  const label = String(payload?.value ?? '')
  const display = label.length > maxChars ? label.slice(0, maxChars - 1) + '…' : label
  return (
    <text
      x={x - 4}
      y={y}
      textAnchor="end"
      dominantBaseline="middle"
      fill="var(--text-muted)"
      fontSize={11}
    >
      {display}
    </text>
  )
}

// B-05: formatter pour grands nombres sur l'axe horizontal
function formatY(v) {
  if (v >= 1_000_000) return `${(v / 1_000_000).toFixed(1)}M`
  if (v >= 1_000) return `${(v / 1_000).toFixed(0)}k`
  return v
}

export function RankingBarChart({ data, xKey, yKey }) {
  const height = Math.max(220, data.length * 48)
  const longestLabel = data.reduce((max, d) => Math.max(max, String(d[xKey] ?? '').length), 0)
  const yWidth = Math.min(180, Math.max(90, longestLabel * 7))
  const maxChars = Math.floor(yWidth / 7)

  return (
    <div className="chart-wrapper" data-chart-type="bar">
      <ResponsiveContainer width="100%" height={height}>
        <BarChart
          data={data}
          layout="vertical"
          margin={{ top: 8, right: 24, left: 8, bottom: 8 }}
        >
          <CartesianGrid strokeDasharray="3 3" stroke="var(--panel-border)" />
          <XAxis type="number" tickFormatter={formatY} tick={{ fill: 'var(--text-muted)', fontSize: 12 }} />
          <YAxis
            type="category"
            dataKey={xKey}
            tick={<YTick maxChars={maxChars} />}
            width={yWidth}
          />
          <Tooltip
            contentStyle={{ background: 'var(--panel-bg)', border: '1px solid var(--panel-border)', borderRadius: '8px' }}
            formatter={(value) => [value.toLocaleString('fr-FR')]}
          />
          <Bar dataKey={yKey} radius={[0, 4, 4, 0]}>
            {data.map((_, i) => (
              <Cell key={i} fill={COLORS[i % COLORS.length]} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  )
}
