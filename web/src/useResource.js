import { useCallback, useEffect, useRef, useState } from 'react'
import { api } from './api.js'

export function useResource(path, dependency) {
  const [data, setData] = useState(null)
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(true)
  const latest = useRef(0)
  const refresh = useCallback(async () => {
    const request = ++latest.current
    setError('')
    setBusy(true)
    try {
      const value = await api(path)
      if (request === latest.current) setData(value)
    } catch (failure) {
      if (request === latest.current) setError(failure.message)
    } finally {
      if (request === latest.current) setBusy(false)
    }
  }, [path])

  useEffect(() => {
    void refresh()
    return () => { latest.current++ }
  }, [refresh, dependency])

  return { data, error, busy, refresh, setData }
}
