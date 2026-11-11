import type { CityProperties, CityProximity } from '../../services/api'

/** Which residents the population figures count */
export type PopulationGroup = 'all' | 'age_5_17'

export const POPULATION_GROUPS: Record<PopulationGroup, { label: string; noun: string; column: string }> = {
  all: { label: 'All residents', noun: 'residents', column: 'Residents' },
  age_5_17: { label: 'Ages 5–17', noun: 'residents aged 5–17', column: 'Ages 5–17' },
}

/** Population of a place in the group (0 if the data is missing) */
export function placePopulation(place: CityProperties, group: PopulationGroup): number {
  return (group === 'all' ? place.population : place.population_5_17) ?? 0
}

/** Population and covered population of one result in the group */
export function resultPopulation(result: CityProximity, group: PopulationGroup) {
  return group === 'all'
    ? { population: result.population, covered: result.covered_population, pct: result.covered_population_pct }
    : {
        population: result.population_5_17 ?? 0,
        covered: result.covered_population_5_17 ?? 0,
        pct: result.covered_population_5_17_pct,
      }
}

/** Ages 5–17 can be shown only if every place has the data (loaded after migration 003) */
export function hasAgeData(places: CityProperties[]): boolean {
  return places.length > 0 && places.every((p) => p.population_5_17 !== null)
}

export interface CoverageSummary {
  places: number
  population: number
  coveredPopulation: number
  areaKm2: number
  coveredAreaKm2: number
  /** Eligible facilities inside the places */
  eligible: number
  /** Facilities inside the places excluded from the analysis (exclusively virtual) */
  excluded: number
  /** Distinct eligible facilities within the radius of any of the places */
  contributing: number
}

/**
 * Combines per-place results. Population and area are summed, so percentages
 * are weighted, not averaged. A school near a shared boundary contributes to
 * both places, so contributing schools are counted once by id.
 */
export function summarizeCoverage(results: CityProximity[], group: PopulationGroup = 'all'): CoverageSummary {
  const contributing = new Set(results.flatMap((r) => r.contributing_facility_ids))
  return results.reduce<CoverageSummary>(
    (sum, r) => {
      const { population, covered } = resultPopulation(r, group)
      return {
        ...sum,
        places: sum.places + 1,
        population: sum.population + population,
        coveredPopulation: sum.coveredPopulation + covered,
        areaKm2: sum.areaKm2 + r.city_area_km2,
        coveredAreaKm2: sum.coveredAreaKm2 + r.covered_area_km2,
        eligible: sum.eligible + r.eligible_facilities,
        excluded: sum.excluded + r.excluded_facilities,
      }
    },
    {
      places: 0,
      population: 0,
      coveredPopulation: 0,
      areaKm2: 0,
      coveredAreaKm2: 0,
      eligible: 0,
      excluded: 0,
      contributing: contributing.size,
    },
  )
}

export function percent(part: number, whole: number): string {
  return whole ? `${((100 * part) / whole).toFixed(1)}%` : '—'
}
