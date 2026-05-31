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

function pickChartKeys(columns, rows) {
  const sample = rows[0] ?? []

  // Label (xKey) : première colonne texte non-identifiant
  const labelIdx = columns.findIndex(
    (col, i) => !/_id$/i.test(col) && isNaN(Number(sample[i]))
  )

  // Valeur (yKey) : dernière colonne numérique qui N'EST PAS un identifiant
  // (un _id comme product_id n'a pas de sens comme métrique sur un graphique)
  let valueIdx = -1
  for (let i = columns.length - 1; i >= 0; i--) {
    const isNumeric = !isNaN(Number(sample[i])) && sample[i] !== null && sample[i] !== ''
    const isId = /_id$/i.test(columns[i])
    if (isNumeric && !isId) {
      valueIdx = i
      break
    }
  }

  if (valueIdx < 0) return null  // Pas de métrique numérique exploitable → pas de graphique

  return {
    xKey: labelIdx >= 0 ? columns[labelIdx] : columns[0],
    yKey: columns[valueIdx],
  }
}

export function ChartRouter({ columns, rows }) {
  const type = detectChartType(columns, rows)
  if (!type) return null

  const data = buildData(columns, rows)

  if (type === 'line') {
    return <SalesLineChart data={data} xKey={columns[0]} yKey={columns[1]} />
  }

  const keys = pickChartKeys(columns, rows)
  if (!keys) return null
  return <RankingBarChart data={data} xKey={keys.xKey} yKey={keys.yKey} />
}
