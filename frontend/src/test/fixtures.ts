import type { CityProperties, FacilityCollection, FacilityProperties } from '../services/api'

type Facility = FacilityCollection['features'][number]

export function makeFacility(overrides: Partial<FacilityProperties> = {}): Facility {
  const properties: FacilityProperties = {
    id: 1,
    name: 'Test Elementary',
    facility_type: 'school',
    facility_subtype: 'Elementary',
    city: 'Redlands',
    address_city: 'Redlands',
    in_study_area: true,
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
      CountyNameGeo: 'San Bernardino',
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

export function makePlace(name: string, overrides: Partial<CityProperties> = {}): CityProperties {
  return {
    name,
    geoid: '0600000',
    place_type: 'city',
    area_km2: 10,
    population: 1000,
    facility_count: 0,
    ...overrides,
  }
}
