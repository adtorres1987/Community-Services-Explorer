import type { FacilityProperties } from '../../services/api'

export type SchoolCategory = 'Elementary' | 'Middle' | 'High' | 'K-12' | 'Other'

// Okabe–Ito palette: distinguishable with common colour-vision deficiencies
export const CATEGORY_COLORS: Record<SchoolCategory, string> = {
  Elementary: '#0072B2',
  Middle: '#E69F00',
  High: '#009E73',
  'K-12': '#CC79A7',
  Other: '#6B6B6B',
}

export const CATEGORIES = Object.keys(CATEGORY_COLORS) as SchoolCategory[]

/** Groups CDE SchoolType values; Continuation, Community Day, etc. become "Other". */
export function schoolCategory(subtype: string | null): SchoolCategory {
  if (subtype === 'Elementary' || subtype === 'Middle' || subtype === 'High' || subtype === 'K-12') {
    return subtype
  }
  return 'Other'
}

const VIRTUAL_LABELS: Record<string, string> = {
  N: 'In person',
  C: 'Primarily in person',
  F: 'Primarily virtual',
  V: 'Exclusively virtual',
}

export function virtualLabel(code: string | null): string {
  return (code && VIRTUAL_LABELS[code]) ?? 'Unknown'
}

function gradeLabel(grade: string | null): string | null {
  if (!grade) return null
  return /^\d+$/.test(grade) ? String(Number(grade)) : grade
}

export function gradeRange(properties: FacilityProperties): string | null {
  const low = gradeLabel(properties.attributes.GradeLow)
  const high = gradeLabel(properties.attributes.GradeHigh)
  if (!low || !high) return null
  return low === high ? low : `${low}–${high}`
}

export interface FacilityFilters {
  /** Selected places; empty means all places */
  cities: string[]
  subtype: string | null
}

/** True when the place is part of the selection (an empty selection includes every place). */
export function isSelected(city: string | null, cities: string[]): boolean {
  return cities.length === 0 || (city !== null && cities.includes(city))
}

/** Schools of other types are hidden: the coverage only uses the selected type. */
export function matchesSubtype(properties: FacilityProperties, subtype: string | null): boolean {
  return subtype === null || properties.facility_subtype === subtype
}

/**
 * Schools drawn at full strength: in the study area and in a selected place.
 * The rest stay on the map, faded, because they still add to the coverage.
 */
export function isInFocus(properties: FacilityProperties, filters: FacilityFilters): boolean {
  return (
    properties.in_study_area &&
    isSelected(properties.city, filters.cities) &&
    matchesSubtype(properties, filters.subtype)
  )
}
