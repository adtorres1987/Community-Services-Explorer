import type { FacilityProperties } from '../../services/api'

// Subtypes written by the pipeline (AM-peak departures per hour at the stop)
export const TRANSIT_CATEGORIES = [
  'Frequent bus (15 min or better)',
  'Bus every 20–30 min',
  'Bus less often',
  'Rail',
] as const

export type TransitCategory = (typeof TRANSIT_CATEGORIES)[number]

export const TRANSIT_COLORS: Record<TransitCategory, string> = {
  'Frequent bus (15 min or better)': '#009E73',
  'Bus every 20–30 min': '#0072B2',
  'Bus less often': '#E69F00',
  Rail: '#CC79A7',
}

const NO_SERVICE_COLOR = '#6B6B6B'

export function transitColor(subtype: string | null): string {
  return TRANSIT_COLORS[subtype as TransitCategory] ?? NO_SERVICE_COLOR
}

const number = new Intl.NumberFormat('en-US', { maximumFractionDigits: 1 })

/** "8 per hour (7–9 am)" */
export function peakFrequency(properties: FacilityProperties): string | null {
  const perHour = properties.attributes.PeakDeparturesPerHour
  return perHour == null ? null : `${number.format(perHour)} per hour (7–9 am)`
}
