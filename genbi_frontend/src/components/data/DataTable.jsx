import { useState } from 'react'
import { Download, Printer, ChevronUp, ChevronDown, ChevronsUpDown } from 'lucide-react'
import { useToast } from '../../hooks/useToast'

const FR_MONTHS = ['janvier','février','mars','avril','mai','juin','juillet','août','septembre','octobre','novembre','décembre']

function formatCell(value) {
  if (value === null || value === undefined) return '—'
  if (typeof value === 'string' && /^\d{4}-\d{2}-\d{2}T/.test(value)) {
    const d = new Date(value)
    if (!isNaN(d)) return `${FR_MONTHS[d.getUTCMonth()]} ${d.getUTCFullYear()}`
  }
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

function SortIcon({ colIdx, sortState }) {
  if (sortState.col !== colIdx) return <ChevronsUpDown size={11} style={{ opacity: 0.35 }} />
  return sortState.dir === 'asc'
    ? <ChevronUp size={11} style={{ color: 'var(--secondary)' }} />
    : <ChevronDown size={11} style={{ color: 'var(--secondary)' }} />
}

export function DataTable({ columns, rows, rowCount }) {
  const [visibleCount, setVisibleCount] = useState(50)
  const [sortState, setSortState] = useState({ col: null, dir: 'asc' })
  const toast = useToast()

  if (!rows || rows.length === 0) {
    return <p className="datatable__empty">Aucun résultat trouvé.</p>
  }

  function toggleSort(colIdx) {
    setSortState(prev =>
      prev.col === colIdx
        ? { col: colIdx, dir: prev.dir === 'asc' ? 'desc' : 'asc' }
        : { col: colIdx, dir: 'asc' }
    )
  }

  const sorted = sortState.col === null ? rows : [...rows].sort((a, b) => {
    const va = a[sortState.col]
    const vb = b[sortState.col]
    const na = Number(va), nb = Number(vb)
    const cmp = !isNaN(na) && !isNaN(nb) && va !== null && vb !== null
      ? na - nb
      : String(va ?? '').localeCompare(String(vb ?? ''), 'fr')
    return sortState.dir === 'asc' ? cmp : -cmp
  })

  const visible = sorted.slice(0, visibleCount)
  const hasMore = visibleCount < sorted.length
  const remaining = Math.min(50, sorted.length - visibleCount)

  function exportCSV() {
    const header = columns.join(';')
    const body = rows
      .map(r => r.map(c => `"${String(c ?? '').replace(/"/g, '""')}"`).join(';'))
      .join('\n')
    const blob = new Blob(['﻿' + header + '\n' + body], { type: 'text/csv;charset=utf-8;' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = 'export.csv'
    a.click()
    URL.revokeObjectURL(url)
    toast?.('Export téléchargé')
  }

  function printTable() {
    window.print()
  }

  const isTruncated = rowCount != null && rowCount > rows.length

  return (
    <div className="datatable__wrapper" data-testid="results-table">
      <div className="datatable__toolbar">
        <span className="datatable__count">{rows.length} ligne{rows.length > 1 ? 's' : ''}</span>
        <div style={{ display: 'flex', gap: '0.4rem' }}>
          <button className="datatable__export-btn" onClick={printTable} title="Imprimer / PDF">
            <Printer size={13} />
            <span>PDF</span>
          </button>
          <button className="datatable__export-btn" onClick={exportCSV} title="Exporter en CSV">
            <Download size={13} />
            <span>CSV</span>
          </button>
        </div>
      </div>
      <table className="datatable">
        <thead>
          <tr>
            {columns.map((col, i) => (
              <th
                key={col}
                className="datatable__th datatable__th--sortable"
                onClick={() => toggleSort(i)}
              >
                <span className="datatable__th-inner">
                  {formatHeader(col)}
                  <SortIcon colIdx={i} sortState={sortState} />
                </span>
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {visible.map((row, i) => (
            <tr key={i} className="datatable__row">
              {row.map((cell, j) => (
                <td key={j} className="datatable__td">{formatCell(cell)}</td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
      {hasMore && (
        <button
          className="datatable__load-more"
          onClick={() => setVisibleCount(c => c + 50)}
        >
          Afficher {remaining} ligne{remaining > 1 ? 's' : ''} suivante{remaining > 1 ? 's' : ''}
        </button>
      )}
      {isTruncated && (
        <p className="datatable__truncated">
          {rows.length} premiers résultats sur {rowCount.toLocaleString('fr-FR')} au total
        </p>
      )}
    </div>
  )
}
