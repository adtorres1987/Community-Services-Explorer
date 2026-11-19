import { CATEGORIES, CATEGORY_COLORS, schoolCategory } from './schools'
import { LIBRARY_COLORS, libraryCategory } from './libraries'
import { TRANSIT_CATEGORIES, TRANSIT_COLORS, transitColor } from './transit'

/** facility_type values in the API */
export type ServiceType = 'school' | 'library' | 'transit'

export interface RadiusOption {
  value: number
  /** Short label for the radius buttons and table headers */
  label: string
  /** Label for sentences, e.g. "1 mile (1.6 km)" */
  long: string
}

export interface ServiceConfig {
  type: ServiceType
  /** Selector label, e.g. "Schools" */
  label: string
  singular: string
  plural: string
  subtypeLabel: string
  allSubtypes: string
  radii: RadiusOption[]
  /** Legend entries, in order */
  categories: { name: string; color: string }[]
  color: (subtype: string | null) => string
  /** Marker radius in pixels, for facilities in focus and the rest */
  marker: { focused: number; faded: number }
  /** Statistics subtitle when a subtype is selected */
  describeSubtype: (subtype: string) => string
  /** Wording for facilities excluded from the analysis, if the service has them */
  excluded?: { legend: string; summary: string; popup: string }
  /** Service-specific opening of the statistics caveat */
  caveat: string
  source: string
}

function metres(value: number): RadiusOption {
  const label = value >= 1000 ? `${value / 1000} km` : `${value} m`
  return { value, label, long: label }
}

export const SERVICES: Record<ServiceType, ServiceConfig> = {
  school: {
    type: 'school',
    label: 'Schools',
    singular: 'school',
    plural: 'schools',
    subtypeLabel: 'School type',
    allSubtypes: 'All school types',
    radii: [500, 1000, 1500, 2000].map(metres),
    categories: CATEGORIES.map((name) => ({ name, color: CATEGORY_COLORS[name] })),
    color: (subtype) => CATEGORY_COLORS[schoolCategory(subtype)],
    marker: { focused: 7, faded: 5 },
    describeSubtype: (subtype) => `${subtype} schools`,
    excluded: {
      legend: 'Exclusively virtual (not in proximity analysis)',
      summary: 'exclusively virtual excluded',
      popup:
        'Exclusively virtual: this is an administrative address, so the school is excluded from the proximity analysis.',
    },
    caveat:
      'Public schools (CDE 2025–26) are assigned to the community whose boundary contains them. ' +
      'Any school of any type and grade level counts.',
    source: 'California Department of Education, California Public Schools 2025–26',
  },
  library: {
    type: 'library',
    label: 'Libraries',
    singular: 'library',
    plural: 'libraries',
    subtypeLabel: 'Library type',
    allSubtypes: 'All library types',
    // Distances common in US library planning, rounded to metres
    radii: [
      { value: 800, label: '½ mi', long: '½ mile (800 m)' },
      { value: 1600, label: '1 mi', long: '1 mile (1.6 km)' },
      { value: 3200, label: '2 mi', long: '2 miles (3.2 km)' },
    ],
    categories: (['Central', 'Branch'] as const).map((name) => ({ name, color: LIBRARY_COLORS[name] })),
    color: (subtype) => LIBRARY_COLORS[libraryCategory(subtype)],
    marker: { focused: 7, faded: 5 },
    describeSubtype: (subtype) => `${subtype} libraries`,
    caveat:
      'Public library outlets (IMLS Public Libraries Survey FY 2024: central and branch ' +
      'libraries; bookmobiles and law libraries are not included) are assigned to the community ' +
      'whose boundary contains them.',
    source: 'Institute of Museum and Library Services, Public Libraries Survey FY 2024',
  },
  transit: {
    type: 'transit',
    label: 'Transit',
    singular: 'transit stop',
    plural: 'transit stops',
    subtypeLabel: 'Service level',
    allSubtypes: 'All service levels',
    // Walking distances used in US transit planning: ¼ mile to a bus stop, ½ mile to rail
    radii: [
      { value: 400, label: '¼ mi', long: '¼ mile (400 m)' },
      { value: 800, label: '½ mi', long: '½ mile (800 m)' },
    ],
    categories: TRANSIT_CATEGORIES.map((name) => ({ name, color: TRANSIT_COLORS[name] })),
    color: transitColor,
    // ~1,250 stops: smaller markers so the coverage stays visible
    marker: { focused: 4, faded: 3 },
    describeSubtype: (subtype) => `Service level: ${subtype}`,
    excluded: {
      legend: 'No weekday service (not in proximity analysis)',
      summary: 'without weekday service excluded',
      popup: 'No departures on the reference weekday, so the stop is excluded from the proximity analysis.',
    },
    caveat:
      'Omnitrans bus stops and Metrolink rail stations (GTFS schedules, weekday of 16 September ' +
      '2026) are assigned to the community whose boundary contains them; service level is the ' +
      'average departures per hour at the stop from 7 to 9 am, all routes and directions.',
    source: 'Omnitrans and Metrolink GTFS schedules (Mobility Database archive)',
  },
}

export const SERVICE_TYPES = Object.keys(SERVICES) as ServiceType[]

/** Radius of the new service closest to the current one; Off stays Off. */
export function closestRadius(radius: number | null, service: ServiceConfig): number | null {
  if (radius === null) return null
  return service.radii.reduce((best, option) =>
    Math.abs(option.value - radius) < Math.abs(best.value - radius) ? option : best,
  ).value
}

export function radiusOption(service: ServiceConfig, radius: number): RadiusOption {
  return service.radii.find((option) => option.value === radius) ?? metres(radius)
}
