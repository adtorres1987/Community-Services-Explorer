import { describe, expect, it } from 'vitest'
import { makePlace, makeResult } from '../../test/fixtures'
import { hasAgeData, percent, summarizeCoverage } from './coverage'

describe('summarizeCoverage', () => {
  const redlands = makeResult({
    city: 'Redlands',
    population: 1000,
    covered_population: 800,
    population_5_17: 200,
    covered_population_5_17: 180,
    city_area_km2: 10,
    covered_area_km2: 4,
    eligible_facilities: 2,
    excluded_facilities: 1,
    contributing_facility_ids: [1, 2, 9],
  })
  const lomaLinda = makeResult({
    city: 'Loma Linda',
    population: 3000,
    covered_population: 600,
    population_5_17: 600,
    covered_population_5_17: 120,
    city_area_km2: 30,
    covered_area_km2: 3,
    eligible_facilities: 1,
    excluded_facilities: 0,
    // School 2 sits near the shared boundary and covers both places
    contributing_facility_ids: [2, 5],
  })

  it('sums population and area so percentages are weighted', () => {
    const summary = summarizeCoverage([redlands, lomaLinda])
    expect(summary).toMatchObject({
      places: 2,
      population: 4000,
      coveredPopulation: 1400,
      areaKm2: 40,
      coveredAreaKm2: 7,
      eligible: 3,
      excluded: 1,
    })
    // Weighted: 1,400 / 4,000 = 35 %, not the mean of 80 % and 20 %
    expect(percent(summary.coveredPopulation, summary.population)).toBe('35.0%')
  })

  it('uses the population aged 5–17 when asked', () => {
    const summary = summarizeCoverage([redlands, lomaLinda], 'age_5_17')
    expect(summary).toMatchObject({ population: 800, coveredPopulation: 300, areaKm2: 40, coveredAreaKm2: 7 })
    expect(percent(summary.coveredPopulation, summary.population)).toBe('37.5%')
  })

  it('counts contributing schools once across places', () => {
    expect(summarizeCoverage([redlands, lomaLinda]).contributing).toBe(4)
  })

  it('handles an empty selection', () => {
    const summary = summarizeCoverage([])
    expect(summary.places).toBe(0)
    expect(summary.contributing).toBe(0)
    expect(percent(summary.coveredPopulation, summary.population)).toBe('—')
  })
})

describe('hasAgeData', () => {
  it('requires the age data for every place', () => {
    expect(hasAgeData([makePlace('A'), makePlace('B')])).toBe(true)
    expect(hasAgeData([makePlace('A'), makePlace('B', { population_5_17: null })])).toBe(false)
    expect(hasAgeData([])).toBe(false)
  })
})
