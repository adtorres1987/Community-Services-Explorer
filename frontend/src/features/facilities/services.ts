import { CATEGORIES, CATEGORY_COLORS, schoolCategory } from './schools'
import { LIBRARY_COLORS, libraryCategory } from './libraries'

/** facility_type values in the API */
export type ServiceType = 'school' | 'library'

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
  /** Legend and summary wording for facilities excluded from the analysis, if the service has them */
  excluded?: { legend: string; summary: string }
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
    excluded: {
      legend: 'Exclusively virtual (not in proximity analysis)',
      summary: 'exclusively virtual excluded',
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
    caveat:
      'Public library outlets (IMLS Public Libraries Survey FY 2024: central and branch ' +
      'libraries; bookmobiles and law libraries are not included) are assigned to the community ' +
      'whose boundary contains them.',
    source: 'Institute of Museum and Library Services, Public Libraries Survey FY 2024',
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
