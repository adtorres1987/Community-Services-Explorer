import { afterEach, describe, expect, it, vi } from 'vitest'
import { ApiError, fetchFacilities, fetchProximity } from './api'

function mockFetch(implementation: (url: URL) => Promise<Response>) {
  const fetchMock = vi.fn(implementation)
  vi.stubGlobal('fetch', fetchMock)
  return fetchMock
}

afterEach(() => vi.unstubAllGlobals())

describe('API client', () => {
  it('sends query parameters and omits empty ones', async () => {
    const fetchMock = mockFetch(async () => Response.json({ results: [] }))
    await fetchProximity(500, 'school', null, new AbortController().signal)

    const url = new URL(String(fetchMock.mock.calls[0][0]))
    expect(url.pathname).toMatch(/\/analysis\/proximity$/)
    expect(url.searchParams.get('radius_m')).toBe('500')
    expect(url.searchParams.get('facility_type')).toBe('school')
    expect(url.searchParams.has('facility_subtype')).toBe(false)
  })

  it('requests the service type and every facility', async () => {
    const fetchMock = mockFetch(async () => Response.json({ features: [] }))
    await fetchProximity(1600, 'library', 'Branch', new AbortController().signal)
    await fetchFacilities(new AbortController().signal)

    const proximity = new URL(String(fetchMock.mock.calls[0][0]))
    expect(proximity.searchParams.get('facility_type')).toBe('library')
    expect(proximity.searchParams.get('facility_subtype')).toBe('Branch')
    const facilities = new URL(String(fetchMock.mock.calls[1][0]))
    expect(facilities.pathname).toMatch(/\/facilities$/)
    expect(facilities.search).toBe('')
  })

  it('uses the API error detail as the message', async () => {
    mockFetch(async () => Response.json({ detail: "City 'Atlantis' not found" }, { status: 404 }))
    const error = await fetchProximity(500, 'school', null, new AbortController().signal).catch(
      (e) => e,
    )
    expect(error).toBeInstanceOf(ApiError)
    expect(error.status).toBe(404)
    expect(error.message).toBe("City 'Atlantis' not found")
  })

  it('reports an unreachable API clearly', async () => {
    mockFetch(async () => {
      throw new TypeError('Failed to fetch')
    })
    await expect(fetchProximity(500, 'school', null, new AbortController().signal)).rejects.toThrow(
      /Cannot reach the API/,
    )
  })
})
