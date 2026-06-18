import { SalesLineChart } from './SalesLineChart'
import { RankingBarChart } from './RankingBarChart'
import { ComboChart } from './ComboChart'
import { GenericsPieChart } from './GenericsPieChart'

function isDateColumn(name) {
  return /date|jour|semaine|mois|month/i.test(name)
}

function isNumeric(sample, colIdx) {
  const v = sample[colIdx]
  return v !== null && v !== undefined && v !== '' && !isNaN(Number(v))
}

function isPieColumn(name) {
  return /généri|generic|princep|type|mode|assur|insur|payment|catégor|répart|segment|classe|forme|thérap/i.test(name)
}

function isBooleanRows(rows) {
  return rows.every(r => {
    const v = r[0]
    return v === true || v === false || v === 0 || v === 1 || v === 'true' || v === 'false'
  })
}

function detectChartType(columns, rows) {
  if (!rows || rows.length <= 1) return null
  if (!columns || columns.length < 2) return null

  if (isDateColumn(columns[0])) {
    const sample = rows[0] ?? []
    const numericCols = columns.slice(1).filter((_, i) => isNumeric(sample, i + 1))
    if (numericCols.length >= 2) return 'combo'
    return 'line'
  }

  // Pie : 2 colonnes + 2-8 lignes + colonne catégorielle reconnue ou valeurs booléennes
  if (
    columns.length === 2 &&
    rows.length >= 2 &&
    rows.length <= 8 &&
    isNumeric(rows[0], 1) &&
    (isPieColumn(columns[0]) || isBooleanRows(rows))
  ) return 'pie'

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

  const labelIdx = columns.findIndex(
    (col, i) => !/_id$/i.test(col) && isNaN(Number(sample[i]))
  )

  let valueIdx = -1
  for (let i = columns.length - 1; i >= 0; i--) {
    const isNum = !isNaN(Number(sample[i])) && sample[i] !== null && sample[i] !== ''
    const isId = /_id$/i.test(columns[i])
    if (isNum && !isId) { valueIdx = i; break }
  }

  if (valueIdx < 0) return null

  return {
    xKey: labelIdx >= 0 ? columns[labelIdx] : columns[0],
    yKey: columns[valueIdx],
  }
}

function pickComboKeys(columns, rows) {
  const sample = rows[0] ?? []
  const numericIdxs = columns
    .map((col, i) => ({ col, i }))
    .filter(({ col, i }) => i > 0 && !/_id$/i.test(col) && isNumeric(sample, i))
  if (numericIdxs.length < 2) return null
  return {
    xKey: columns[0],
    barKey: numericIdxs[0].col,
    lineKey: numericIdxs[1].col,
  }
}

export function ChartRouter({ columns, rows }) {
  const type = detectChartType(columns, rows)
  if (!type) return null

  const data = buildData(columns, rows)

  if (type === 'pie') {
    return <GenericsPieChart rows={rows} labelCol={columns[0]} />
  }

  if (type === 'combo') {
    const keys = pickComboKeys(columns, rows)
    if (!keys) return <SalesLineChart data={data} xKey={columns[0]} yKey={columns[1]} />
    return <ComboChart data={data} xKey={keys.xKey} barKey={keys.barKey} lineKey={keys.lineKey} />
  }

  if (type === 'line') {
    const keys = pickChartKeys(columns, rows)
    const yKey = keys ? keys.yKey : columns[1]
    return <SalesLineChart data={data} xKey={columns[0]} yKey={yKey} />
  }

  const keys = pickChartKeys(columns, rows)
  if (!keys) return <p className="chart-empty">Visualisation non disponible pour ce résultat.</p>
  return <RankingBarChart data={data} xKey={keys.xKey} yKey={keys.yKey} />
}
