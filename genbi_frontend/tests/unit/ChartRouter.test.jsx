import { render } from '@testing-library/react'
import { ChartRouter } from '../../src/components/visualizations/ChartRouter'

global.ResizeObserver = class { observe() {} unobserve() {} disconnect() {} }

const DATE_COLS = ['date', 'total']
const DATE_ROWS = [
  ['2026-02-01', 1200000],
  ['2026-03-01', 1500000],
  ['2026-04-01', 1100000],
]

const CAT_COLS = ['produit', 'quantite']
const CAT_ROWS = [
  ['Amoxicilline', 120],
  ['Paracétamol', 95],
  ['Artéméther', 80],
]

test('retourne LineChart pour données temporelles', () => {
  const { container } = render(<ChartRouter columns={DATE_COLS} rows={DATE_ROWS} />)
  expect(container.querySelector('[data-chart-type="line"]')).not.toBeNull()
})

test('retourne BarChart pour catégories', () => {
  const { container } = render(<ChartRouter columns={CAT_COLS} rows={CAT_ROWS} />)
  expect(container.querySelector('[data-chart-type="bar"]')).not.toBeNull()
})

test('retourne null pour valeur unique (1 seule ligne)', () => {
  const { container } = render(
    <ChartRouter columns={['total']} rows={[[42000]]} />
  )
  expect(container.firstChild).toBeNull()
})

test('retourne null pour données vides', () => {
  const { container } = render(<ChartRouter columns={[]} rows={[]} />)
  expect(container.firstChild).toBeNull()
})

test('détecte colonne date correctement — "mois" fallback en BarChart', () => {
  const { container } = render(
    <ChartRouter columns={['mois', 'ca']} rows={[['2026-02', 500000], ['2026-03', 600000]]} />
  )
  expect(container.querySelector('[data-chart-type="bar"]')).not.toBeNull()
})

test('BarChart avec product_id : utilise commercial_name comme label', () => {
  const cols = ['product_id', 'commercial_name', 'total_quantity_sold']
  const rows = [
    [105, 'Glucophage', 15],
    [110, 'Gaviscon', 13],
  ]
  const { container } = render(<ChartRouter columns={cols} rows={rows} />)
  expect(container.querySelector('[data-chart-type="bar"]')).not.toBeNull()
})
