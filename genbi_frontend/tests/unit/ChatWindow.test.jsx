import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { vi } from 'vitest'
import { ChatWindow } from '../../src/components/chat/ChatWindow'
import * as hooks from '../../src/hooks/useChat'

vi.mock('../../src/hooks/useChat')
vi.mock('../../src/services/api', () => ({
  chatApi: { executeSQL: vi.fn(), sendFeedback: vi.fn() },
}))

const defaultHook = {
  messages: [],
  status: 'idle',
  sendQuestion: vi.fn(),
  setFeedback: vi.fn(),
}

beforeEach(() => {
  vi.clearAllMocks()
  hooks.useChat.mockReturnValue(defaultHook)
})

test('input vide au démarrage', () => {
  render(<ChatWindow />)
  expect(screen.getByTestId('query-input').value).toBe('')
})

test('submit appelle sendQuestion avec la question', async () => {
  const sendQuestion = vi.fn()
  hooks.useChat.mockReturnValue({ ...defaultHook, sendQuestion })

  render(<ChatWindow />)
  fireEvent.change(screen.getByTestId('query-input'), { target: { value: 'Mon CA ?' } })
  fireEvent.click(screen.getByTestId('send-button'))

  await waitFor(() => expect(sendQuestion).toHaveBeenCalledWith('Mon CA ?'))
})

test('affiche spinner pendant loading', () => {
  hooks.useChat.mockReturnValue({ ...defaultHook, status: 'loading' })
  render(<ChatWindow />)
  expect(screen.getByTestId('loading-indicator')).toBeInTheDocument()
})

test('affiche les messages de la conversation', () => {
  hooks.useChat.mockReturnValue({
    ...defaultHook,
    messages: [
      { id: 0, role: 'user', content: 'Quel est mon CA ?' },
      { id: 1, role: 'ai', sql: 'SELECT 1', columns: ['ca'], rows: [[42]], insight: 'Bonne perf.', error: null, feedback: null },
    ],
  })
  render(<ChatWindow />)
  expect(screen.getByText('Quel est mon CA ?')).toBeInTheDocument()
  expect(screen.getByText('Bonne perf.')).toBeInTheDocument()
  expect(screen.getByTestId('results-table')).toBeInTheDocument()
})

test('affiche erreur dans le message ai concerné', () => {
  hooks.useChat.mockReturnValue({
    ...defaultHook,
    messages: [
      { id: 0, role: 'user', content: 'Question' },
      { id: 1, role: 'ai', error: 'Erreur serveur', feedback: null },
    ],
  })
  render(<ChatWindow />)
  expect(screen.getByText('Erreur serveur')).toBeInTheDocument()
})
