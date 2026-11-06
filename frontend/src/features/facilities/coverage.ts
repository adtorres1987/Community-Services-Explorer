import type { CityProximity } from '../../services/api'

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
export function summarizeCoverage(results: CityProximity[]): CoverageSummary {
  const contributing = new Set(results.flatMap((r) => r.contributing_facility_ids))
  return results.reduce<CoverageSummary>(
    (sum, r) => ({
      ...sum,
      places: sum.places + 1,
      population: sum.population + r.population,
      coveredPopulation: sum.coveredPopulation + r.covered_population,
      areaKm2: sum.areaKm2 + r.city_area_km2,
      coveredAreaKm2: sum.coveredAreaKm2 + r.covered_area_km2,
      eligible: sum.eligible + r.eligible_facilities,
      excluded: sum.excluded + r.excluded_facilities,
    }),
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
