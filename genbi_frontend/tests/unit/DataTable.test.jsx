import { render, screen } from '@testing-library/react'
import { DataTable } from '../../src/components/data/DataTable'

const COLS = ['produit', 'ca_total']
const ROWS = [
  ['Amoxicilline', 4500000],
  ['Paracétamol', 2100000],
]

test('affiche les colonnes en Title Case', () => {
  render(<DataTable columns={COLS} rows={ROWS} />)
  // formatHeader transforme snake_case → Title Case
  expect(screen.getByText('Produit')).toBeInTheDocument()
  expect(screen.getByText('Ca Total')).toBeInTheDocument()
})

test('affiche les lignes', () => {
  render(<DataTable columns={COLS} rows={ROWS} />)
  expect(screen.getByText('Amoxicilline')).toBeInTheDocument()
  expect(screen.getByText('Paracétamol')).toBeInTheDocument()
})

test('formate les montants avec séparateurs', () => {
  const { container } = render(<DataTable columns={COLS} rows={ROWS} />)
  const cells = container.querySelectorAll('td')
  // 4500000 formaté → séparateur présent (longueur > 7 chiffres seuls)
  const raw = cells[1].textContent
  expect(raw.replace(/\D/g, '')).toBe('4500000') // chiffres corrects
  expect(raw.length).toBeGreaterThan(7)           // au moins 2 séparateurs ajoutés
})

test('tableau vide affiche message', () => {
  render(<DataTable columns={COLS} rows={[]} />)
  expect(screen.getByText(/aucun résultat/i)).toBeInTheDocument()
})
