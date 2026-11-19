import type { FacilityProperties } from '../../services/api'

export interface FacilityFilters {
  /** Selected places; empty means all places */
  cities: string[]
  subtype: string | null
}

/** True when the place is part of the selection (an empty selection includes every place). */
export function isSelected(city: string | null, cities: string[]): boolean {
  return cities.length === 0 || (city !== null && cities.includes(city))
}

/** Facilities of other subtypes are hidden: the coverage only uses the selected subtype. */
export function matchesSubtype(properties: FacilityProperties, subtype: string | null): boolean {
  return subtype === null || properties.facility_subtype === subtype
}

/**
 * Facilities drawn at full strength: in the study area and in a selected place.
 * The rest stay on the map, faded, because they still add to the coverage.
 */
export function isInFocus(properties: FacilityProperties, filters: FacilityFilters): boolean {
  return (
    properties.in_study_area &&
    isSelected(properties.city, filters.cities) &&
    matchesSubtype(properties, filters.subtype)
  )
}
