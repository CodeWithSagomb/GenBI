import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
} from 'recharts'

export function RankingBarChart({ data, xKey, yKey }) {
  return (
    <div className="chart-wrapper" data-chart-type="bar">
      <ResponsiveContainer width="100%" height={280}>
        <BarChart
          data={data}
          layout="vertical"
          margin={{ top: 8, right: 24, left: 80, bottom: 8 }}
        >
          <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.08)" />
          <XAxis type="number" tick={{ fill: 'var(--text-muted)', fontSize: 12 }} />
          <YAxis
            type="category"
            dataKey={xKey}
            tick={{ fill: 'var(--text-muted)', fontSize: 12 }}
            width={76}
          />
          <Tooltip
            contentStyle={{ background: 'var(--panel-bg)', border: '1px solid var(--panel-border)' }}
          />
          <Bar dataKey={yKey} fill="var(--primary)" radius={[0, 4, 4, 0]} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  )
}
