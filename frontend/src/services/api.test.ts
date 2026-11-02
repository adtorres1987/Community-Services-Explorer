import { afterEach, describe, expect, it, vi } from 'vitest'
import { ApiError, fetchProximity } from './api'

function mockFetch(implementation: (url: URL) => Promise<Response>) {
  const fetchMock = vi.fn(implementation)
  vi.stubGlobal('fetch', fetchMock)
  return fetchMock
}

afterEach(() => vi.unstubAllGlobals())

describe('API client', () => {
  it('sends query parameters and omits empty ones', async () => {
    const fetchMock = mockFetch(async () => Response.json({ results: [] }))
    await fetchProximity(500, null, new AbortController().signal)

    const url = new URL(String(fetchMock.mock.calls[0][0]))
    expect(url.pathname).toMatch(/\/analysis\/proximity$/)
    expect(url.searchParams.get('radius_m')).toBe('500')
    expect(url.searchParams.get('facility_type')).toBe('school')
    expect(url.searchParams.has('facility_subtype')).toBe(false)
  })

  it('uses the API error detail as the message', async () => {
    mockFetch(async () => Response.json({ detail: "City 'Atlantis' not found" }, { status: 404 }))
    const error = await fetchProximity(500, null, new AbortController().signal).catch((e) => e)
    expect(error).toBeInstanceOf(ApiError)
    expect(error.status).toBe(404)
    expect(error.message).toBe("City 'Atlantis' not found")
  })

  it('reports an unreachable API clearly', async () => {
    mockFetch(async () => {
      throw new TypeError('Failed to fetch')
    })
    await expect(fetchProximity(500, null, new AbortController().signal)).rejects.toThrow(
      /Cannot reach the API/,
    )
  })
})
