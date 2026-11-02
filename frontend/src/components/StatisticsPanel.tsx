import type { FacilityCollection, ProximityResponse } from '../services/api'
import type { RequestState } from '../services/useRequest'

interface Props {
  cityNames: string[]
  selectedCity: string | null
  subtype: string | null
  // All facilities matching the type filter, so both cities can be compared
  facilities: FacilityCollection['features']
  radius: number | null
  proximity: RequestState<ProximityResponse>
}

function formatRadius(radius: number) {
  return radius >= 1000 ? `${radius / 1000} km` : `${radius} m`
}

export function StatisticsPanel({
  cityNames,
  selectedCity,
  subtype,
  facilities,
  radius,
  proximity,
}: Props) {
  const results = proximity.data?.results ?? []

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
            <th scope="col">City</th>
            <th scope="col">Schools</th>
            <th scope="col">In city limits</th>
            {radius !== null && <th scope="col">Area within {formatRadius(radius)}</th>}
          </tr>
        </thead>
        <tbody>
          {cityNames.map((name) => {
            const inCity = facilities.filter((f) => f.properties.city === name)
            const result = results.find((r) => r.city === name)
            return (
              <tr key={name} className={name === selectedCity ? 'is-selected' : undefined}>
                <th scope="row">{name}</th>
                <td>{inCity.length}</td>
                <td>{inCity.filter((f) => f.properties.in_city_limits).length}</td>
                {radius !== null && <td>{result ? `${result.covered_pct}%` : '—'}</td>}
              </tr>
            )
          })}
        </tbody>
      </table>

      {proximity.error && (
        <p className="error" role="alert">
          Proximity analysis failed: {proximity.error}{' '}
          <button type="button" onClick={proximity.retry}>
            Retry
          </button>
        </p>
      )}

      {radius !== null &&
        results
          .filter((r) => selectedCity === null || r.city === selectedCity)
          .map((r) => (
            <p key={r.city} className="stats-detail">
              <strong>{r.city}:</strong> {r.covered_area_km2} of {r.city_area_km2} km² lies within{' '}
              {formatRadius(radius)} of {r.eligible_facilities} school
              {r.eligible_facilities === 1 ? '' : 's'}
              {r.excluded_facilities > 0 &&
                ` (${r.excluded_facilities} exclusively virtual excluded)`}
              .
            </p>
          ))}

      <p className="caveat">
        Schools are counted by address city. Proximity is straight-line distance, not travel by
        street, and says nothing about capacity, quality or enrolment boundaries.
      </p>
    </section>
  )
}
