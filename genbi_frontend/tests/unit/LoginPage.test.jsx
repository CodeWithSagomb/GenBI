import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { vi } from 'vitest'
import { LoginPage } from '../../src/components/auth/LoginPage'
import * as api from '../../src/services/api'

vi.mock('../../src/services/api', () => ({
  authApi: {
    login: vi.fn(),
  },
}))

beforeEach(() => {
  vi.clearAllMocks()
  localStorage.clear()
})

test('affiche formulaire email + mot de passe', () => {
  render(<LoginPage onLogin={vi.fn()} />)
  expect(screen.getByLabelText(/email/i)).toBeInTheDocument()
  expect(screen.getByLabelText(/mot de passe/i)).toBeInTheDocument()
  expect(screen.getByRole('button', { name: /connexion/i })).toBeInTheDocument()
})

test('login réussi stocke le token et appelle onLogin', async () => {
  api.authApi.login.mockResolvedValue({ access_token: 'tok_abc', token_type: 'bearer' })
  const onLogin = vi.fn()

  render(<LoginPage onLogin={onLogin} />)
  fireEvent.change(screen.getByLabelText(/email/i), { target: { value: 'bourguiba@pharma.sn' } })
  fireEvent.change(screen.getByLabelText(/mot de passe/i), { target: { value: 'test123' } })
  fireEvent.click(screen.getByRole('button', { name: /connexion/i }))

  await waitFor(() => {
    expect(localStorage.getItem('genbi_token')).toBe('tok_abc')
    expect(onLogin).toHaveBeenCalledOnce()
  })
})

test('mauvais credentials affiche un message d\'erreur', async () => {
  api.authApi.login.mockRejectedValue(new Error('Email ou mot de passe incorrect.'))

  render(<LoginPage onLogin={vi.fn()} />)
  fireEvent.change(screen.getByLabelText(/email/i), { target: { value: 'x@x.com' } })
  fireEvent.change(screen.getByLabelText(/mot de passe/i), { target: { value: 'mauvais' } })
  fireEvent.click(screen.getByRole('button', { name: /connexion/i }))

  await waitFor(() => expect(screen.getByRole('alert')).toBeInTheDocument())
  expect(screen.getByRole('alert').textContent).toContain('Email ou mot de passe incorrect.')
})

test('bouton désactivé pendant le chargement', async () => {
  api.authApi.login.mockImplementation(() => new Promise(() => {}))

  render(<LoginPage onLogin={vi.fn()} />)
  fireEvent.change(screen.getByLabelText(/email/i), { target: { value: 'a@b.com' } })
  fireEvent.change(screen.getByLabelText(/mot de passe/i), { target: { value: '123' } })
  fireEvent.click(screen.getByRole('button', { name: /connexion/i }))

  await waitFor(() => expect(screen.getByRole('button', { name: /connexion/i })).toBeDisabled())
})
