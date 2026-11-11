import { useMemo, useState } from 'react'
import { FilterPanel } from './components/FilterPanel'
import { Legend } from './components/Legend'
import { MapView } from './components/MapView'
import { StatisticsPanel } from './components/StatisticsPanel'
import { hasAgeData, type PopulationGroup } from './features/facilities/coverage'
import { isInFocus, isSelected, matchesSubtype } from './features/facilities/schools'
import { fetchCities, fetchFacilities, fetchProximity } from './services/api'
import { useRequest } from './services/useRequest'

export default function App() {
  // Selected communities; empty means all
  const [selectedCities, setSelectedCities] = useState<string[]>([])
  const [subtype, setSubtype] = useState<string | null>(null)
  const [radius, setRadius] = useState<number | null>(null)
  const [populationGroup, setPopulationGroup] = useState<PopulationGroup>('all')

  const cities = useRequest('cities', fetchCities)
  const facilities = useRequest('facilities', fetchFacilities)
  const proximity = useRequest(
    radius === null ? null : `proximity:${radius}:${subtype ?? ''}`,
    (signal) => fetchProximity(radius ?? 0, subtype, signal),
  )

  const allFacilities = useMemo(() => facilities.data?.features ?? [], [facilities.data])
  const places = useMemo(() => cities.data?.features.map((f) => f.properties) ?? [], [cities.data])
  // Until the places load, keep the option enabled rather than flash a warning
  const ageDataAvailable = places.length === 0 || hasAgeData(places)
  const group = ageDataAvailable ? populationGroup : 'all'
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
        visible
          .filter((f) => isInFocus(f.properties, { cities: selectedCities, subtype }))
          .map((f) => f.properties.id),
      ),
    [visible, selectedCities, subtype],
  )
  // The statistics panel applies the community selection itself
  const studySchools = useMemo(() => visible.filter((f) => f.properties.in_study_area), [visible])
  const coverage = (proximity.data?.results ?? []).filter((r) => isSelected(r.city, selectedCities))
  const scope =
    selectedCities.length === 0 || selectedCities.length === places.length
      ? 'the study area'
      : selectedCities.length === 1
        ? selectedCities[0]
        : `${selectedCities.length} communities`

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
            selectedCities={selectedCities}
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
              {focusedIds.size} school{focusedIds.size === 1 ? '' : 's'} in {scope}
            </div>
          )}
        </div>

        <aside className="sidebar">
          <FilterPanel
            places={places}
            subtypes={subtypes}
            cities={selectedCities}
            subtype={subtype}
            radius={radius}
            populationGroup={group}
            ageDataAvailable={ageDataAvailable}
            onCitiesChange={setSelectedCities}
            onSubtypeChange={setSubtype}
            onRadiusChange={setRadius}
            onPopulationGroupChange={setPopulationGroup}
          />
          <StatisticsPanel
            places={places}
            selectedCities={selectedCities}
            subtype={subtype}
            populationGroup={group}
            facilities={studySchools}
            radius={radius}
            proximity={proximity}
          />
          <Legend />
          <footer className="sources">
            Data: California Department of Education, California Public Schools 2025–26;
            U.S. Census Bureau, TIGER/Line 2026 Places, 2020 Census blocks, P.L. 94-171
            population and DHC ages 5–17.
          </footer>
        </aside>
      </main>
    </div>
  )
}
