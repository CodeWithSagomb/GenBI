import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
} from 'recharts'

// Custom tick rendu hors du clipPath SVG de recharts — évite le problème
// de l'espace disparaissant quand un caractère accentué (é, è…) tombe
// exactement à la frontière du clip (ex: "OméprazoleBiogaran" → espace perdu).
function YTick({ x, y, payload }) {
  const label = String(payload?.value ?? '')
  const MAX = 22
  const display = label.length > MAX ? label.slice(0, MAX - 1) + '…' : label
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
  return (
    <div className="chart-wrapper" data-chart-type="bar">
      <ResponsiveContainer width="100%" height={280}>
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
            tick={<YTick />}
            width={160}
          />
          <Tooltip
            contentStyle={{ background: 'var(--panel-bg)', border: '1px solid var(--panel-border)', borderRadius: '8px' }}
            formatter={(value) => [value.toLocaleString('fr-FR')]}
          />
          <Bar dataKey={yKey} fill="var(--primary)" radius={[0, 4, 4, 0]} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  )
}
