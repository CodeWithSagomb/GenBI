import { render, screen, fireEvent } from '@testing-library/react'
import { vi } from 'vitest'
import { FeedbackButtons } from '../../src/components/chat/FeedbackButtons'

test('affiche les deux boutons actifs par défaut', () => {
  render(<FeedbackButtons onFeedback={vi.fn()} feedback={null} />)
  expect(screen.getByRole('button', { name: /👍/ })).not.toBeDisabled()
  expect(screen.getByRole('button', { name: /👎/ })).not.toBeDisabled()
})

test('clic 👍 appelle onFeedback("good")', () => {
  const onFeedback = vi.fn()
  render(<FeedbackButtons onFeedback={onFeedback} feedback={null} />)
  fireEvent.click(screen.getByRole('button', { name: /👍/ }))
  expect(onFeedback).toHaveBeenCalledWith('good')
})

test('clic 👎 appelle onFeedback("bad")', () => {
  const onFeedback = vi.fn()
  render(<FeedbackButtons onFeedback={onFeedback} feedback={null} />)
  fireEvent.click(screen.getByRole('button', { name: /👎/ }))
  expect(onFeedback).toHaveBeenCalledWith('bad')
})

test('après vote, les deux boutons sont désactivés', () => {
  render(<FeedbackButtons onFeedback={vi.fn()} feedback="good" />)
  expect(screen.getByRole('button', { name: /👍/ })).toBeDisabled()
  expect(screen.getByRole('button', { name: /👎/ })).toBeDisabled()
})

test('confirmation visible après vote', () => {
  render(<FeedbackButtons onFeedback={vi.fn()} feedback="good" />)
  expect(screen.getByText(/merci/i)).toBeInTheDocument()
})
