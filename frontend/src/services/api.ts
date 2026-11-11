// Types mirror the Pydantic schemas in backend/app/schemas.
import type { FeatureCollection, MultiPolygon, Point, Polygon } from 'geojson'

// Absolute URL in development; '/api' (same origin, proxied by nginx) in the Docker build
const API_URL = (import.meta.env.VITE_API_URL ?? 'http://localhost:8010').replace(/\/$/, '')

export interface SchoolAttributes {
  SchoolLevel: string | null
  GradeLow: string | null
  GradeHigh: string | null
  Charter: string | null
  Virtual: string | null
  DistrictName: string | null
  Street: string | null
  Zip: string | null
  CountyNameGeo: string | null
  Website: string | null
  EnrollTotal: number | null
}

export interface FacilityProperties {
  id: number
  name: string
  facility_type: string
  facility_subtype: string | null
  /** Study place containing the facility; null outside the study area */
  city: string | null
  /** Mailing-address city from the source */
  address_city: string | null
  /** False: nearby facility that only contributes to proximity coverage */
  in_study_area: boolean
  proximity_eligible: boolean
  attributes: SchoolAttributes
}

export type FacilityCollection = FeatureCollection<Point, FacilityProperties>

export interface CityProperties {
  name: string
  geoid: string
  /** "city" or "CDP" (unincorporated census-designated place) */
  place_type: string
  area_km2: number
  population: number
  /** Aged 5–17 (2020 DHC); null if the database predates migration 003 */
  population_5_17: number | null
  facility_count: number
}

export type CityCollection = FeatureCollection<MultiPolygon, CityProperties>

export interface CityProximity {
  city: string
  eligible_facilities: number
  excluded_facilities: number
  /** Eligible facilities anywhere within the radius, including neighbouring places */
  contributing_facilities: number
  /** Their ids, to count distinct facilities across several places */
  contributing_facility_ids: number[]
  city_area_km2: number
  covered_area_km2: number
  covered_pct: number
  population: number
  covered_population: number
  covered_population_pct: number
  population_5_17: number | null
  covered_population_5_17: number | null
  covered_population_5_17_pct: number | null
  coverage: Polygon | MultiPolygon | null
}

export interface ProximityResponse {
  radius_m: number
  facility_type: string | null
  facility_subtype: string | null
  method: string
  results: CityProximity[]
}

export class ApiError extends Error {
  status: number | undefined

  constructor(message: string, status?: number) {
    super(message)
    this.name = 'ApiError'
    this.status = status
  }
}

type Params = Record<string, string | number | null | undefined>

async function getJson<T>(path: string, params: Params, signal: AbortSignal): Promise<T> {
  const url = new URL(API_URL + path, window.location.origin)
  for (const [key, value] of Object.entries(params)) {
    if (value !== null && value !== undefined) url.searchParams.set(key, String(value))
  }

  let response: Response
  try {
    response = await fetch(url, { signal })
  } catch (error) {
    if (signal.aborted) throw error
    throw new ApiError(`Cannot reach the API at ${API_URL}. Is it running?`)
  }

  if (!response.ok) {
    let detail = `${response.status} ${response.statusText}`
    try {
      const body = await response.json()
      if (typeof body.detail === 'string') detail = body.detail
    } catch {
      // Keep the status text when the body is not JSON
    }
    throw new ApiError(detail, response.status)
  }
  return response.json() as Promise<T>
}

export function fetchCities(signal: AbortSignal) {
  return getJson<CityCollection>('/cities', {}, signal)
}

export function fetchFacilities(signal: AbortSignal) {
  return getJson<FacilityCollection>('/facilities', { facility_type: 'school' }, signal)
}

export function fetchProximity(
  radiusM: number,
  facilitySubtype: string | null,
  signal: AbortSignal,
) {
  return getJson<ProximityResponse>(
    '/analysis/proximity',
    { radius_m: radiusM, facility_type: 'school', facility_subtype: facilitySubtype },
    signal,
  )
}
