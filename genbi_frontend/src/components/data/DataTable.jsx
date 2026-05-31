function formatCell(value) {
  if (value === null || value === undefined) return '—'
  // PostgreSQL NUMERIC/DECIMAL arrive en string depuis JSON — convertir avant le test
  const num = Number(value)
  if (!isNaN(num) && String(value).trim() !== '') {
    const abs = Math.abs(num)
    if (abs > 999) {
      const rounded = Math.round(num * 100) / 100
      const [int, dec] = rounded.toFixed(2).split('.')
      const formatted = int.replace(/\B(?=(\d{3})+(?!\d))/g, ' ')
      return dec === '00' ? formatted : `${formatted},${dec}`
    }
  }
  return String(value)
}

function formatHeader(col) {
  return col.split('_').map((w) => w.charAt(0).toUpperCase() + w.slice(1)).join(' ')
}

export function DataTable({ columns, rows }) {
  if (!rows || rows.length === 0) {
    return (
      <p className="datatable__empty">Aucun résultat trouvé.</p>
    )
  }

  return (
    <div className="datatable__wrapper" data-testid="results-table">
      <table className="datatable">
        <thead>
          <tr>
            {columns.map((col) => (
              <th key={col} className="datatable__th">{formatHeader(col)}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row, i) => (
            <tr key={i} className="datatable__row">
              {row.map((cell, j) => (
                <td key={j} className="datatable__td">{formatCell(cell)}</td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
