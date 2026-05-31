import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { vi } from 'vitest'
import { SQLDisplay } from '../../src/components/chat/SQLDisplay'

const SQL = 'SELECT product_name, SUM(total_amount) FROM marts.fct_sales GROUP BY 1'

test('affiche le SQL reçu', () => {
  render(<SQLDisplay sql={SQL} />)
  expect(screen.getByText(SQL)).toBeInTheDocument()
})

test('SQL est dans un élément pre', () => {
  render(<SQLDisplay sql={SQL} />)
  expect(screen.getByRole('code')).toBeInTheDocument()
})

test('affiche rien si sql est null', () => {
  const { container } = render(<SQLDisplay sql={null} />)
  expect(container.firstChild).toBeNull()
})

test('bouton Modifier est visible', () => {
  render(<SQLDisplay sql={SQL} onReexecute={vi.fn()} />)
  expect(screen.getByRole('button', { name: /modifier/i })).toBeInTheDocument()
})

test('clic Modifier ouvre un éditeur textarea', async () => {
  render(<SQLDisplay sql={SQL} onReexecute={vi.fn()} />)
  await userEvent.click(screen.getByRole('button', { name: /modifier/i }))
  expect(screen.getByRole('textbox')).toBeInTheDocument()
})
