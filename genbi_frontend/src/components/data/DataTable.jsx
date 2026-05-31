function formatCell(value) {
  if (typeof value === 'number' && value > 999) {
    return Math.round(value).toString().replace(/\B(?=(\d{3})+(?!\d))/g, ' ')
  }
  if (value === null || value === undefined) return '—'
  return String(value)
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
              <th key={col} className="datatable__th">{col}</th>
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
