import React from 'react'
import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import App from './App.jsx'
import { api } from './api.js'

vi.mock('./api.js', async importOriginal => ({ ...(await importOriginal()), api: vi.fn() }))
vi.mock('./VaultScene.jsx', () => ({ default: () => <div>Vault illustration</div> }))

const session = { user: { id: 'admin-id', username: 'admin', role: 'Admin' }, csrf: 'test-token',
  summary: { expires: 2000000000, key_fingerprint: 'fingerprint' } }
const file = (id, name = 'duplicate.txt') => ({ id, name, owner: 'admin-id', uploaded_by: 'admin',
  size: 10, shared: 0, created: 100, digest: 'a'.repeat(64) })

beforeEach(() => {
  vi.resetAllMocks()
  window.scrollTo = vi.fn()
  globalThis.IntersectionObserver = class { observe() {} unobserve() {} disconnect() {} }
})
afterEach(cleanup)

function backend(resource, logout = async () => ({ signed_out: true })) {
  api.mockImplementation(async (path, options) => {
    if (path === '/status') return { initialized: true }
    if (path === '/session') return session
    if (path === '/logout') return logout()
    return resource(path, options)
  })
}

describe('failed requests remain recoverable', () => {
  it.each([['vault', '/files'], ['team', '/users'], ['monitor', '/monitoring']])(
    '%s shows an error instead of rendering null data', async (page, endpoint) => {
      window.history.replaceState(null, '', '/app/' + page)
      backend(async path => { if (path === endpoint) throw new Error('Service temporarily unavailable') })
      render(<App />)
      await screen.findByText('Service temporarily unavailable')
      expect(screen.getByRole('button', { name: 'Try again' })).toBeTruthy()
    })

  it('a successful retry clears the old error and displays the files', async () => {
    window.history.replaceState(null, '', '/app/vault')
    let failed = true
    backend(async path => {
      if (path === '/files') {
        if (failed) throw new Error('Service temporarily unavailable')
        return [file('one', 'recovered.txt')]
      }
    })
    render(<App />)
    await screen.findByText('Service temporarily unavailable')
    failed = false
    fireEvent.click(screen.getByRole('button', { name: 'Try again' }))
    await screen.findByText('Repository Index')
    expect(screen.queryByText('Service temporarily unavailable')).toBeNull()
    expect(screen.getAllByText('recovered.txt').length).toBeGreaterThan(0)
  })
})

it('Account Settings sign-out ends the session and opens sign-in', async () => {
  window.history.replaceState(null, '', '/app/account')
  backend(async path => path === '/sessions' ? [] : undefined)
  render(<App />)
  await screen.findByText('Account Settings', { selector: 'h1' })
  fireEvent.click(screen.getByRole('button', { name: 'Sign out', exact: true }))
  await screen.findByText('Unlock Workspace')
  expect(api).toHaveBeenCalledWith('/logout', expect.objectContaining({ method: 'POST', csrf: 'test-token' }))
  expect(window.location.pathname).toBe('/signin')
})

it('batch verification distinguishes IDs even when filenames are identical', async () => {
  window.history.replaceState(null, '', '/app/vault')
  backend(async path => {
    if (path === '/files') return [file('good'), file('bad')]
    if (path === '/files/good/verify') return { sha256: 'a'.repeat(64) }
    if (path === '/files/bad/verify') throw new Error('Integrity verification failed')
  })
  render(<App />)
  await screen.findByText('Repository Index')
  fireEvent.click(screen.getByRole('button', { name: 'Batch verify' }))
  await screen.findByText(/1 verified; 1 failed/)
  expect(screen.getByText('Verified during this session')).toBeTruthy()
  fireEvent.click(screen.getAllByRole('row')[2])
  expect(screen.queryByText('Verified during this session')).toBeNull()
})

it('a failed recheck removes an earlier successful verification indicator', async () => {
  window.history.replaceState(null, '', '/app/vault')
  let tampered = false
  backend(async path => {
    if (path === '/files') return [file('one')]
    if (path === '/files/one/verify') {
      if (tampered) throw new Error('Integrity verification failed')
      return { sha256: 'a'.repeat(64) }
    }
  })
  render(<App />)
  await screen.findByText('Repository Index')
  fireEvent.click(screen.getByRole('button', { name: 'Verify integrity now' }))
  await screen.findByText('Verified during this session')
  await waitFor(() => expect(screen.getByRole('button', { name: 'Verify integrity now' }).disabled).toBe(false))
  tampered = true
  fireEvent.click(screen.getByRole('button', { name: 'Verify integrity now' }))
  await screen.findByText('Integrity verification failed')
  expect(screen.queryByText('Verified during this session')).toBeNull()
})

it('the default landing preview does not request a missing optional image', async () => {
  window.history.replaceState(null, '', '/')
  backend(async () => undefined)
  render(<App />)
  await screen.findByText('Security you can demonstrate.')
  expect(screen.queryByAltText('CipherVault file vault preview')).toBeNull()
})

it('a failed download cannot keep a previous verification indicator', async () => {
  window.history.replaceState(null, '', '/app/vault')
  backend(async path => {
    if (path === '/files') return [file('one')]
    if (path === '/files/one/verify') return { sha256: 'a'.repeat(64) }
    if (path === '/files/one/download') throw new Error('Integrity verification failed')
  })
  render(<App />)
  await screen.findByText('Repository Index')
  fireEvent.click(screen.getByRole('button', { name: 'Verify integrity now' }))
  await screen.findByText('Verified during this session')
  await waitFor(() => expect(screen.getByRole('button', { name: 'Verify integrity now' }).disabled).toBe(false))
  fireEvent.click(screen.getByRole('button', { name: 'Download verified file' }))
  await screen.findByText('Integrity verification failed')
  expect(screen.queryByText('Verified during this session')).toBeNull()
})

it('a network failure during logout keeps the account visible and offers a retry', async () => {
  window.history.replaceState(null, '', '/app/account')
  let offline = true
  backend(async path => path === '/sessions' ? [] : undefined, async () => {
    if (offline) throw new Error('Failed to fetch')
    return { signed_out: true }
  })
  render(<App />)
  await screen.findByText('Account Settings', { selector: 'h1' })
  fireEvent.click(screen.getByRole('button', { name: 'Sign out', exact: true }))
  await screen.findByText(/Sign-out failed/)
  expect(window.location.pathname).toBe('/app/account')
  offline = false
  fireEvent.click(screen.getByRole('button', { name: 'Sign out', exact: true }))
  await screen.findByText('Unlock Workspace')
})

it('logout of an already expired session still returns to sign-in', async () => {
  window.history.replaceState(null, '', '/app/account')
  backend(async path => path === '/sessions' ? [] : undefined, async () => {
    throw Object.assign(new Error('Session expired'), { status: 401 })
  })
  render(<App />)
  await screen.findByText('Account Settings', { selector: 'h1' })
  fireEvent.click(screen.getByRole('button', { name: 'Sign out', exact: true }))
  await screen.findByText('Unlock Workspace')
})
