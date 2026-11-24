import React from 'react'
import { act, cleanup, fireEvent, render, screen } from '@testing-library/react'
import { afterEach, beforeEach, expect, it, vi } from 'vitest'
import VaultTerminal from './VaultTerminal.jsx'

let reduced = false
let change
beforeEach(() => {
  vi.useFakeTimers()
  reduced = false
  window.matchMedia = vi.fn(() => ({ matches: reduced, addEventListener: (_, fn) => { change = fn }, removeEventListener: vi.fn() }))
})
afterEach(() => { cleanup(); vi.useRealTimers() })

it('shows a labeled sample, pauses, resumes, completes and replays', () => {
  render(<VaultTerminal/>)
  expect(screen.getByText(/Illustrative walkthrough/)).toBeTruthy()
  act(() => vi.advanceTimersByTime(900))
  expect(screen.getByText('1 / 4')).toBeTruthy()
  fireEvent.click(screen.getByRole('button', { name: 'Pause walkthrough' }))
  act(() => vi.advanceTimersByTime(5000))
  expect(screen.getByText('1 / 4')).toBeTruthy()
  fireEvent.click(screen.getByRole('button', { name: 'Resume walkthrough' }))
  for (let i = 0; i < 3; i++) act(() => vi.advanceTimersByTime(900))
  expect(screen.getByText('4 / 4')).toBeTruthy()
  fireEvent.click(screen.getByRole('button', { name: 'Replay walkthrough' }))
  expect(screen.getByText('0 / 4')).toBeTruthy()
})

it('shows all steps without timers for reduced motion, including preference changes', () => {
  reduced = true
  render(<VaultTerminal compact/>)
  expect(screen.getByText('4 / 4')).toBeTruthy()
  expect(screen.queryByRole('button', { name: /walkthrough/ })).toBeNull()
  expect(vi.getTimerCount()).toBe(0)
  act(() => change({ matches: false }))
  expect(screen.getByRole('button', { name: 'Replay walkthrough' })).toBeTruthy()
})

it('cleans up pending timers when removed', () => {
  const view = render(<VaultTerminal/>)
  view.unmount()
  expect(vi.getTimerCount()).toBe(0)
})
