import { afterEach, expect, it, vi } from 'vitest'
import { api } from './api.js'

afterEach(() => vi.unstubAllGlobals())

it('API errors retain their HTTP status so expired sessions are distinguished from server failures', async () => {
  vi.stubGlobal('fetch', vi.fn(async () => ({ ok: false, status: 401,
    json: async () => ({ detail: 'Session expired. Sign in again.' }) })))
  await expect(api('/logout', { method: 'POST' })).rejects.toMatchObject({
    status: 401, message: 'Session expired. Sign in again.',
  })
})
