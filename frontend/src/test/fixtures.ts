import type { FacilityCollection, FacilityProperties } from '../services/api'

type Facility = FacilityCollection['features'][number]

export function makeFacility(overrides: Partial<FacilityProperties> = {}): Facility {
  const properties: FacilityProperties = {
    id: 1,
    name: 'Test Elementary',
    facility_type: 'school',
    facility_subtype: 'Elementary',
    city: 'Redlands',
    in_city_limits: true,
    proximity_eligible: true,
    attributes: {
      SchoolLevel: 'Elementary',
      GradeLow: 'KG',
      GradeHigh: '05',
      Charter: 'N',
      Virtual: 'N',
      DistrictName: 'Redlands Unified',
      Street: '1 Main St.',
      Zip: '92373',
      Website: 'https://example.org',
      EnrollTotal: 512,
    },
    ...overrides,
  }
  return {
    type: 'Feature',
    id: properties.id,
    geometry: { type: 'Point', coordinates: [-117.18, 34.05] },
    properties,
  }
}
