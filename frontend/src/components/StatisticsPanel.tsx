import type { CityProperties, FacilityCollection, ProximityResponse } from '../services/api'
import type { RequestState } from '../services/useRequest'
import {
  percent,
  placePopulation,
  POPULATION_GROUPS,
  resultPopulation,
  summarizeCoverage,
  type PopulationGroup,
} from '../features/facilities/coverage'
import { isSelected } from '../features/facilities/schools'

interface Props {
  places: CityProperties[]
  /** Selected places; empty means all */
  selectedCities: string[]
  subtype: string | null
  populationGroup: PopulationGroup
  // Study-area facilities matching the type filter
  facilities: FacilityCollection['features']
  radius: number | null
  proximity: RequestState<ProximityResponse>
}

function formatRadius(radius: number) {
  return radius >= 1000 ? `${radius / 1000} km` : `${radius} m`
}

const number = new Intl.NumberFormat('en-US')

export function StatisticsPanel({
  places,
  selectedCities,
  subtype,
  populationGroup,
  facilities,
  radius,
  proximity,
}: Props) {
  const group = POPULATION_GROUPS[populationGroup]
  const shown = places.filter((p) => isSelected(p.name, selectedCities))
  const isPartial = shown.length < places.length
  const shownNames = new Set(shown.map((p) => p.name))
  const results = (proximity.data?.results ?? []).filter((r) => shownNames.has(r.city))
  const summary = summarizeCoverage(results, populationGroup)
  const showCoverage = radius !== null
  const schoolsIn = (name: string) => facilities.filter((f) => f.properties.city === name).length
  const totalSchools = shown.reduce((sum, p) => sum + schoolsIn(p.name), 0)
  const totalPopulation = shown.reduce((sum, p) => sum + placePopulation(p, populationGroup), 0)
  const totalLabel = isPartial ? `Selected (${shown.length})` : `All (${shown.length})`
  const outside = summary.contributing - summary.eligible

  return (
    <section className="panel" aria-labelledby="stats-heading">
      <h2 id="stats-heading">
        Statistics
        {proximity.loading && <span className="muted"> · calculating…</span>}
      </h2>
      <p className="muted">{subtype ? `${subtype} schools` : 'All school types'}</p>

      <table className="stats-table">
        <thead>
          <tr>
            <th scope="col">Community</th>
            <th scope="col">Schools</th>
            {showCoverage ? (
              <>
                <th scope="col">
                  {group.column} within {formatRadius(radius)}
                </th>
                <th scope="col">Area within {formatRadius(radius)}</th>
              </>
            ) : (
              <th scope="col">{populationGroup === 'all' ? 'Population' : group.column} (2020)</th>
            )}
          </tr>
        </thead>
        <tbody>
          {shown.map((place) => {
            const result = results.find((r) => r.city === place.name)
            const pct = result && resultPopulation(result, populationGroup).pct
            return (
              <tr key={place.name}>
                <th scope="row">
                  {place.name}
                  {place.place_type === 'CDP' && <span className="tag">CDP</span>}
                </th>
                <td>{schoolsIn(place.name)}</td>
                {showCoverage ? (
                  <>
                    <td>{pct != null ? `${pct.toFixed(1)}%` : '—'}</td>
                    <td>{result ? `${result.covered_pct.toFixed(1)}%` : '—'}</td>
                  </>
                ) : (
                  <td>{number.format(placePopulation(place, populationGroup))}</td>
                )}
              </tr>
            )
          })}
        </tbody>
        {/* A single place needs no total row */}
        {shown.length > 1 && (
          <tfoot>
            <tr>
              <th scope="row">{totalLabel}</th>
              <td>{totalSchools}</td>
              {showCoverage ? (
                <>
                  <td>{results.length ? percent(summary.coveredPopulation, summary.population) : '—'}</td>
                  <td>{results.length ? percent(summary.coveredAreaKm2, summary.areaKm2) : '—'}</td>
                </>
              ) : (
                <td>{number.format(totalPopulation)}</td>
              )}
            </tr>
          </tfoot>
        )}
      </table>

      {proximity.error && (
        <p className="error" role="alert">
          Proximity analysis failed: {proximity.error}{' '}
          <button type="button" onClick={proximity.retry}>
            Retry
          </button>
        </p>
      )}

      {showCoverage && results.length > 0 && (
        <p className="stats-detail">
          <strong>
            {shown.length === 1 ? shown[0].name : isPartial ? `${shown.length} selected communities` : 'All communities'}
            :
          </strong>{' '}
          {number.format(summary.coveredPopulation)} of {number.format(summary.population)} {group.noun}{' '}
          ({percent(summary.coveredPopulation, summary.population)}) and{' '}
          {summary.coveredAreaKm2.toFixed(2)} of {summary.areaKm2.toFixed(2)} km² are within{' '}
          {formatRadius(radius)} of a school. {summary.contributing} school
          {summary.contributing === 1 ? '' : 's'} contribute
          {summary.contributing === 1 ? 's' : ''}
          {outside > 0 &&
            `, including ${outside} outside ${
              shown.length === 1 ? shown[0].name : isPartial ? 'the selection' : 'the study area'
            }`}
          {summary.excluded > 0 && `; ${summary.excluded} exclusively virtual excluded`}.
        </p>
      )}

      <p className="caveat">
        Schools are assigned to the community whose boundary contains them. Proximity is
        straight-line distance, not travel by street. Residents are 2020 census block counts,
        apportioned by area; ages 5–17 come from the 2020 DHC (table P12), whose block counts
        carry disclosure-avoidance noise that largely averages out over a community. Totals are
        weighted by population and area. Nothing here measures capacity, quality or enrolment
        boundaries.
      </p>
    </section>
  )
}
