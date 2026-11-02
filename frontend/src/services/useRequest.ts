import { useEffect, useRef, useState } from 'react'

export interface RequestState<T> {
  data: T | undefined
  error: string | undefined
  loading: boolean
  retry: () => void
}

interface Result<T> {
  id: string
  data?: T
  error?: string
}

/**
 * Runs `request` whenever `key` changes and aborts the previous call.
 * A null key skips the request. The last data is kept while a new request loads.
 */
export function useRequest<T>(
  key: string | null,
  request: (signal: AbortSignal) => Promise<T>,
): RequestState<T> {
  const [attempt, setAttempt] = useState(0)
  const [result, setResult] = useState<Result<T>>()
  const requestRef = useRef(request)
  const requestId = key === null ? null : `${key}#${attempt}`

  // Always call the latest closure without making it an effect dependency
  useEffect(() => {
    requestRef.current = request
  })

  useEffect(() => {
    if (requestId === null) return
    const controller = new AbortController()
    requestRef.current(controller.signal).then(
      (data) => setResult({ id: requestId, data }),
      (err: unknown) => {
        if (controller.signal.aborted) return
        setResult({ id: requestId, error: err instanceof Error ? err.message : String(err) })
      },
    )
    return () => controller.abort()
  }, [requestId])

  return {
    data: key === null ? undefined : result?.data,
    error: result?.id === requestId ? result?.error : undefined,
    loading: requestId !== null && result?.id !== requestId,
    retry: () => setAttempt((n) => n + 1),
  }
}
