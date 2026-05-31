import { SalesLineChart } from './SalesLineChart'
import { RankingBarChart } from './RankingBarChart'

function isDateColumn(name) {
  return /date|jour|semaine/i.test(name)
}

function detectChartType(columns, rows) {
  if (!rows || rows.length <= 1) return null
  if (!columns || columns.length < 2) return null

  if (isDateColumn(columns[0])) return 'line'
  return 'bar'
}

function buildData(columns, rows) {
  return rows.map((row) => {
    const obj = {}
    columns.forEach((col, i) => { obj[col] = row[i] })
    return obj
  })
}

export function ChartRouter({ columns, rows }) {
  const type = detectChartType(columns, rows)
  if (!type) return null

  const data = buildData(columns, rows)
  const xKey = columns[0]
  const yKey = columns[1]

  if (type === 'line') return <SalesLineChart data={data} xKey={xKey} yKey={yKey} />
  return <RankingBarChart data={data} xKey={xKey} yKey={yKey} />
}
