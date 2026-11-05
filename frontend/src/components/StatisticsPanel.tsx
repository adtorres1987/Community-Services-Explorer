import type { CityProperties, CityProximity, FacilityCollection, ProximityResponse } from '../services/api'
import type { RequestState } from '../services/useRequest'

interface Props {
  places: CityProperties[]
  selectedCity: string | null
  subtype: string | null
  // Study-area facilities matching the type filter, so all places can be compared
  facilities: FacilityCollection['features']
  radius: number | null
  proximity: RequestState<ProximityResponse>
}

function formatRadius(radius: number) {
  return radius >= 1000 ? `${radius / 1000} km` : `${radius} m`
}

function percent(part: number, whole: number) {
  return whole ? `${((100 * part) / whole).toFixed(1)}%` : '—'
}

const number = new Intl.NumberFormat('en-US')

function totals(results: CityProximity[]) {
  return results.reduce(
    (sum, r) => ({
      population: sum.population + r.population,
      covered_population: sum.covered_population + r.covered_population,
      area: sum.area + r.city_area_km2,
      covered_area: sum.covered_area + r.covered_area_km2,
    }),
    { population: 0, covered_population: 0, area: 0, covered_area: 0 },
  )
}

export function StatisticsPanel({
  places,
  selectedCity,
  subtype,
  facilities,
  radius,
  proximity,
}: Props) {
  const results = proximity.data?.results ?? []
  const showCoverage = radius !== null
  const all = totals(results)
  const allPopulation = places.reduce((sum, p) => sum + p.population, 0)
  const detail = results.find((r) => r.city === selectedCity)

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
                <th scope="col">Residents within {formatRadius(radius)}</th>
                <th scope="col">Area within {formatRadius(radius)}</th>
              </>
            ) : (
              <th scope="col">Population (2020)</th>
            )}
          </tr>
        </thead>
        <tbody>
          {places.map((place) => {
            const result = results.find((r) => r.city === place.name)
            const schools = facilities.filter((f) => f.properties.city === place.name).length
            return (
              <tr key={place.name} className={place.name === selectedCity ? 'is-selected' : undefined}>
                <th scope="row">
                  {place.name}
                  {place.place_type === 'CDP' && <span className="tag">CDP</span>}
                </th>
                <td>{schools}</td>
                {showCoverage ? (
                  <>
                    <td>{result ? `${result.covered_population_pct.toFixed(1)}%` : '—'}</td>
                    <td>{result ? `${result.covered_pct.toFixed(1)}%` : '—'}</td>
                  </>
                ) : (
                  <td>{number.format(place.population)}</td>
                )}
              </tr>
            )
          })}
        </tbody>
        <tfoot>
          <tr>
            <th scope="row">All</th>
            <td>{facilities.length}</td>
            {showCoverage ? (
              <>
                <td>{results.length ? percent(all.covered_population, all.population) : '—'}</td>
                <td>{results.length ? percent(all.covered_area, all.area) : '—'}</td>
              </>
            ) : (
              <td>{number.format(allPopulation)}</td>
            )}
          </tr>
        </tfoot>
      </table>

      {proximity.error && (
        <p className="error" role="alert">
          Proximity analysis failed: {proximity.error}{' '}
          <button type="button" onClick={proximity.retry}>
            Retry
          </button>
        </p>
      )}

      {showCoverage && detail && (
        <p className="stats-detail">
          <strong>{detail.city}:</strong> {number.format(detail.covered_population)} of{' '}
          {number.format(detail.population)} residents and {detail.covered_area_km2} of{' '}
          {detail.city_area_km2} km² are within {formatRadius(radius)} of a school.{' '}
          {detail.contributing_facilities} school
          {detail.contributing_facilities === 1 ? '' : 's'} contribute
          {detail.contributing_facilities === 1 ? 's' : ''}, including{' '}
          {detail.contributing_facilities - detail.eligible_facilities} outside {detail.city}
          {detail.excluded_facilities > 0 &&
            `; ${detail.excluded_facilities} exclusively virtual excluded`}
          .
        </p>
      )}

      <p className="caveat">
        Schools are assigned to the community whose boundary contains them. Proximity is
        straight-line distance, not travel by street. Residents are 2020 census block counts,
        apportioned by area. Nothing here measures capacity, quality or enrolment boundaries.
      </p>
    </section>
  )
}
