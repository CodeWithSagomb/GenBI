import { renderHook, act } from '@testing-library/react'
import { vi } from 'vitest'
import { useChat } from '../../src/hooks/useChat'
import * as api from '../../src/services/api'

vi.mock('../../src/services/api', () => ({
  chatApi: {
    sendQuestion: vi.fn(),
    executeSQL: vi.fn(),
    interpret: vi.fn(),
  },
}))

const { chatApi } = api

beforeEach(() => vi.clearAllMocks())

test('état initial est idle', () => {
  const { result } = renderHook(() => useChat())
  expect(result.current.status).toBe('idle')
  expect(result.current.sql).toBeNull()
  expect(result.current.rows).toEqual([])
})

test('sendQuestion passe en loading', async () => {
  chatApi.sendQuestion.mockReturnValue(new Promise(() => {})) // ne résout jamais
  const { result } = renderHook(() => useChat())
  act(() => { result.current.sendQuestion('Quel est mon CA ?') })
  expect(result.current.status).toBe('loading')
})

test('sendQuestion succès stocke sql et résultats', async () => {
  chatApi.sendQuestion.mockResolvedValue({ sql: 'SELECT 1' })
  chatApi.executeSQL.mockResolvedValue({ columns: ['total'], rows: [[42]], row_count: 1 })
  chatApi.interpret.mockResolvedValue({ insight: 'Bonne performance.' })

  const { result } = renderHook(() => useChat())
  await act(async () => { await result.current.sendQuestion('Quel est mon CA ?') })

  expect(result.current.status).toBe('success')
  expect(result.current.sql).toBe('SELECT 1')
  expect(result.current.columns).toEqual(['total'])
  expect(result.current.rows).toEqual([[42]])
  expect(result.current.insight).toBe('Bonne performance.')
})

test('sendQuestion erreur stocke message erreur', async () => {
  chatApi.sendQuestion.mockRejectedValue(new Error('Erreur LLM'))

  const { result } = renderHook(() => useChat())
  await act(async () => { await result.current.sendQuestion('Quel est mon CA ?') })

  expect(result.current.status).toBe('error')
  expect(result.current.error).toBe('Erreur LLM')
})

test('question vide ne déclenche pas appel API', async () => {
  const { result } = renderHook(() => useChat())
  await act(async () => { await result.current.sendQuestion('   ') })

  expect(chatApi.sendQuestion).not.toHaveBeenCalled()
  expect(result.current.status).toBe('idle')
})
