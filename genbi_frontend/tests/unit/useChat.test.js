import { renderHook, act } from '@testing-library/react'
import { vi } from 'vitest'
import { useChat } from '../../src/hooks/useChat'
import * as api from '../../src/services/api'

vi.mock('../../src/services/api', () => ({
  chatApi: {
    analyse: vi.fn(),
    sendFeedback: vi.fn(),
  },
}))

const { chatApi } = api

const mockSimple = (sql = 'SELECT 1', columns = ['total'], rows = [[42]], insight = 'Bonne performance.') => ({
  is_compound: false,
  sub_analyses: [{ sql, columns, rows, row_count: rows.length, insight, question: 'Quel est mon CA ?' }],
})

beforeEach(() => vi.clearAllMocks())

// ── État initial ──────────────────────────────────────────────────────────────

test('état initial : messages vide et status idle', () => {
  const { result } = renderHook(() => useChat())
  expect(result.current.messages).toEqual([])
  expect(result.current.status).toBe('idle')
})

// ── Question vide ─────────────────────────────────────────────────────────────

test('question vide ne déclenche pas appel API', async () => {
  const { result } = renderHook(() => useChat())
  await act(async () => { await result.current.sendQuestion('   ') })
  expect(chatApi.analyse).not.toHaveBeenCalled()
  expect(result.current.messages).toHaveLength(0)
})

// ── Flux succès ───────────────────────────────────────────────────────────────

test('succès : 2 messages ajoutés (user + ai)', async () => {
  chatApi.analyse.mockResolvedValue(mockSimple())

  const { result } = renderHook(() => useChat())
  await act(async () => { await result.current.sendQuestion('Quel est mon CA ?') })

  expect(result.current.messages).toHaveLength(2)
  expect(result.current.messages[0].role).toBe('user')
  expect(result.current.messages[0].content).toBe('Quel est mon CA ?')
  expect(result.current.messages[1].role).toBe('ai')
  expect(result.current.messages[1].is_compound).toBe(false)
  expect(result.current.messages[1].sub_analyses[0].sql).toBe('SELECT 1')
  expect(result.current.messages[1].sub_analyses[0].columns).toEqual(['total'])
  expect(result.current.messages[1].sub_analyses[0].rows).toEqual([[42]])
  expect(result.current.messages[1].sub_analyses[0].insight).toBe('Bonne performance.')
  expect(result.current.messages[1].error).toBeNull()
  expect(result.current.messages[1].feedback).toBeNull()
  expect(result.current.status).toBe('idle')
})

// ── Flux erreur ───────────────────────────────────────────────────────────────

test('erreur : message ai avec champ error, status revient idle', async () => {
  chatApi.analyse.mockRejectedValue(new Error('Erreur LLM'))

  const { result } = renderHook(() => useChat())
  await act(async () => { await result.current.sendQuestion('Quel est mon CA ?') })

  expect(result.current.messages).toHaveLength(2)
  expect(result.current.messages[1].role).toBe('ai')
  expect(result.current.messages[1].error).toBe('Erreur LLM')
  expect(result.current.status).toBe('idle')
})

// ── Historique ────────────────────────────────────────────────────────────────

test('deux questions accumulent 4 messages', async () => {
  chatApi.analyse.mockResolvedValue(mockSimple())

  const { result } = renderHook(() => useChat())
  await act(async () => { await result.current.sendQuestion('Question 1') })
  await act(async () => { await result.current.sendQuestion('Question 2') })

  expect(result.current.messages).toHaveLength(4)
  expect(result.current.messages[0].content).toBe('Question 1')
  expect(result.current.messages[2].content).toBe('Question 2')
})

// ── Feedback ──────────────────────────────────────────────────────────────────

test('setFeedback met à jour feedback du message ciblé', async () => {
  chatApi.analyse.mockResolvedValue(mockSimple())

  const { result } = renderHook(() => useChat())
  await act(async () => { await result.current.sendQuestion('Question') })

  const aiMsg = result.current.messages[1]
  expect(aiMsg.feedback).toBeNull()

  act(() => { result.current.setFeedback(aiMsg.id, 'good') })

  expect(result.current.messages[1].feedback).toBe('good')
})
