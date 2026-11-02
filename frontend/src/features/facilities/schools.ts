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
  city: string | null
  subtype: string | null
}

export function matchesFilters(properties: FacilityProperties, filters: FacilityFilters): boolean {
  return (
    (filters.city === null || properties.city === filters.city) &&
    (filters.subtype === null || properties.facility_subtype === filters.subtype)
  )
}
