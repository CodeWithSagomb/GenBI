import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { vi } from 'vitest'
import { ChatWindow } from '../../src/components/chat/ChatWindow'
import * as useChatModule from '../../src/hooks/useChat'

vi.mock('../../src/hooks/useChat')
vi.mock('../../src/hooks/useSchema', () => ({
  useSchema: () => ({ schema: 'mocked', loading: false, error: null }),
}))

const mockSendQuestion = vi.fn()

function setupHook(overrides = {}) {
  useChatModule.useChat.mockReturnValue({
    status: 'idle',
    question: '',
    sql: null,
    columns: [],
    rows: [],
    row_count: 0,
    insight: null,
    error: null,
    sendQuestion: mockSendQuestion,
    reset: vi.fn(),
    ...overrides,
  })
}

beforeEach(() => {
  vi.clearAllMocks()
  setupHook()
})

test('input vide au démarrage', () => {
  render(<ChatWindow />)
  expect(screen.getByTestId('query-input').value).toBe('')
})

test('submit avec question appelle sendQuestion', async () => {
  render(<ChatWindow />)
  await userEvent.type(screen.getByTestId('query-input'), 'Quel est mon CA ?')
  await userEvent.click(screen.getByTestId('send-button'))
  expect(mockSendQuestion).toHaveBeenCalledWith('Quel est mon CA ?')
})

test('affiche spinner pendant loading', () => {
  setupHook({ status: 'loading' })
  render(<ChatWindow />)
  expect(screen.getByTestId('loading-indicator')).toBeInTheDocument()
})

test('affiche erreur si API échoue', () => {
  setupHook({ status: 'error', error: 'Erreur LLM' })
  render(<ChatWindow />)
  expect(screen.getByText(/Erreur LLM/i)).toBeInTheDocument()
})

test('affiche résultats après succès', () => {
  setupHook({
    status: 'success',
    sql: 'SELECT 1',
    columns: ['total'],
    rows: [[42]],
    row_count: 1,
  })
  render(<ChatWindow />)
  expect(screen.getByTestId('results-table')).toBeInTheDocument()
  expect(screen.getByTestId('sql-display')).toBeInTheDocument()
})
