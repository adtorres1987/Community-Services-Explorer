import { useMemo, useState } from 'react'
import { FilterPanel } from './components/FilterPanel'
import { Legend } from './components/Legend'
import { MapView } from './components/MapView'
import { StatisticsPanel } from './components/StatisticsPanel'
import { isInFocus, matchesSubtype } from './features/facilities/schools'
import { fetchCities, fetchFacilities, fetchProximity } from './services/api'
import { useRequest } from './services/useRequest'

export default function App() {
  const [city, setCity] = useState<string | null>(null)
  const [subtype, setSubtype] = useState<string | null>(null)
  const [radius, setRadius] = useState<number | null>(null)

  const cities = useRequest('cities', fetchCities)
  const facilities = useRequest('facilities', fetchFacilities)
  const proximity = useRequest(
    radius === null ? null : `proximity:${radius}:${subtype ?? ''}`,
    (signal) => fetchProximity(radius ?? 0, subtype, signal),
  )

  const allFacilities = useMemo(() => facilities.data?.features ?? [], [facilities.data])
  const places = useMemo(() => cities.data?.features.map((f) => f.properties) ?? [], [cities.data])
  const subtypes = useMemo(
    () =>
      [...new Set(allFacilities.map((f) => f.properties.facility_subtype))]
        .filter((s): s is string => s !== null)
        .sort(),
    [allFacilities],
  )
  // Every school of the selected type stays on the map: neighbours add to the coverage
  const visible = useMemo(
    () => allFacilities.filter((f) => matchesSubtype(f.properties, subtype)),
    [allFacilities, subtype],
  )
  const focusedIds = useMemo(
    () =>
      new Set(
        visible.filter((f) => isInFocus(f.properties, { city, subtype })).map((f) => f.properties.id),
      ),
    [visible, city, subtype],
  )
  // Statistics compare all places, so they only apply the type filter
  const studySchools = useMemo(() => visible.filter((f) => f.properties.in_study_area), [visible])
  const coverage = (proximity.data?.results ?? []).filter(
    (r) => city === null || r.city === city,
  )

  const loading = cities.loading || facilities.loading
  const loadError = cities.error ?? facilities.error

  return (
    <div className="app">
      <header className="app-header">
        <h1>Community Services Explorer</h1>
        <p>Public schools in nine San Bernardino Valley communities, California</p>
      </header>

      <main className="layout">
        <div className="map-area">
          <MapView
            cities={cities.data}
            facilities={visible}
            focusedIds={focusedIds}
            coverage={coverage}
            selectedCity={city}
          />
          {loading && <div className="map-status">Loading map data…</div>}
          {loadError && (
            <div className="map-status map-status--error" role="alert">
              <p>Could not load data: {loadError}</p>
              <button
                type="button"
                onClick={() => {
                  cities.retry()
                  facilities.retry()
                }}
              >
                Retry
              </button>
            </div>
          )}
          {!loading && !loadError && (
            <div className="map-count" aria-live="polite">
              {focusedIds.size} school{focusedIds.size === 1 ? '' : 's'} in{' '}
              {city ?? 'the study area'}
            </div>
          )}
        </div>

        <aside className="sidebar">
          <FilterPanel
            cities={places.map((p) => p.name)}
            subtypes={subtypes}
            city={city}
            subtype={subtype}
            radius={radius}
            onCityChange={setCity}
            onSubtypeChange={setSubtype}
            onRadiusChange={setRadius}
          />
          <StatisticsPanel
            places={places}
            selectedCity={city}
            subtype={subtype}
            facilities={studySchools}
            radius={radius}
            proximity={proximity}
          />
          <Legend />
          <footer className="sources">
            Data: California Department of Education, California Public Schools 2025–26;
            U.S. Census Bureau, TIGER/Line 2026 Places, 2020 Census blocks and P.L. 94-171
            population.
          </footer>
        </aside>
      </main>
    </div>
  )
}
