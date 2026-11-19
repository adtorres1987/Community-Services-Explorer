import type { FacilityProperties } from '../../services/api'

export type LibraryCategory = 'Central' | 'Branch'

export const LIBRARY_COLORS: Record<LibraryCategory, string> = {
  Central: '#0072B2',
  Branch: '#E69F00',
}

/** PLS outlet types kept by the pipeline: central and branch libraries. */
export function libraryCategory(subtype: string | null): LibraryCategory {
  return subtype === 'Central' ? 'Central' : 'Branch'
}

const number = new Intl.NumberFormat('en-US')

/** "2,384 h/year (52 weeks)" from the PLS annual hours and weeks open. */
export function openingHours(properties: FacilityProperties): string | null {
  const { AnnualHours: hours, WeeksOpen: weeks } = properties.attributes
  if (hours == null) return null
  return weeks != null ? `${number.format(hours)} h/year (${weeks} weeks)` : `${number.format(hours)} h/year`
}

export function floorArea(properties: FacilityProperties): string | null {
  const { SquareFeet: squareFeet } = properties.attributes
  return squareFeet == null ? null : `${number.format(squareFeet)} sq ft`
}
