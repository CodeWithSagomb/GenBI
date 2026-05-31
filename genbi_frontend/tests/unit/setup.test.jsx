// Valide que l'infrastructure Vitest + jsdom + jest-dom est opérationnelle
import { render } from '@testing-library/react'

test('jest-dom matchers sont disponibles', () => {
  const div = document.createElement('div')
  div.textContent = 'GenBI'
  document.body.appendChild(div)
  expect(div).toBeInTheDocument()
  document.body.removeChild(div)
})

test('render RTL fonctionne', () => {
  const { getByText } = render(<p>Pharmacie Bourguiba</p>)
  expect(getByText('Pharmacie Bourguiba')).toBeInTheDocument()
})
