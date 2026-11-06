import { useEffect } from 'react'
import { geoJSON } from 'leaflet'
import { CircleMarker, GeoJSON, MapContainer, Pane, Popup, TileLayer, useMap } from 'react-leaflet'
import type { CityCollection, CityProximity, FacilityCollection } from '../services/api'
import { CATEGORY_COLORS, isSelected, schoolCategory } from '../features/facilities/schools'
import {
  BASEMAP,
  BOUNDARY_STYLE,
  COVERAGE_STYLE,
  INITIAL_CENTER,
  INITIAL_ZOOM,
} from '../maps/basemap'
import { FacilityPopup } from './FacilityPopup'

interface Props {
  cities: CityCollection | undefined
  facilities: FacilityCollection['features']
  /** Facilities drawn at full strength; the others are faded */
  focusedIds: Set<number>
  coverage: CityProximity[]
  /** Selected places; empty means all */
  selectedCities: string[]
}

function FitToCities({ cities, selectionKey }: { cities: CityCollection; selectionKey: string }) {
  const map = useMap()

  useEffect(() => {
    const selected = selectionKey ? selectionKey.split('|') : []
    const features = cities.features.filter((f) => isSelected(f.properties.name, selected))
    if (features.length === 0) return
    map.fitBounds(geoJSON(features).getBounds(), {
      padding: [24, 24],
    })
    // Keyed by the selection string, not the array, so it only refits when the selection changes
  }, [map, cities, selectionKey])

  return null
}

export function MapView({ cities, facilities, focusedIds, coverage, selectedCities }: Props) {
  const selectionKey = selectedCities.join('|')
  return (
    <MapContainer
      center={INITIAL_CENTER}
      zoom={INITIAL_ZOOM}
      // Fractional zoom lets fitBounds fill narrow (mobile) maps instead of jumping a level out
      zoomSnap={0.25}
      className="map"
      aria-label="Map of schools in the study communities"
    >
      <TileLayer {...BASEMAP} />

      {/* Panes fix the draw order: coverage below boundaries below school markers */}
      <Pane name="coverage" style={{ zIndex: 350 }}>
        {coverage.map(
          (result) =>
            result.coverage && (
              // GeoJSON layers are immutable in react-leaflet; the key re-creates them on change
              <GeoJSON
                key={`${result.city}:${result.covered_area_km2}`}
                data={result.coverage}
                style={COVERAGE_STYLE}
                interactive={false}
              />
            ),
        )}
      </Pane>

      <Pane name="boundaries" style={{ zIndex: 380 }}>
        {cities && (
          <GeoJSON
            // Re-created when the selection changes so unselected boundaries can be dimmed
            key={selectionKey}
            data={cities}
            style={(feature) => ({
              ...BOUNDARY_STYLE,
              opacity: isSelected(feature?.properties.name, selectedCities) ? 1 : 0.35,
            })}
            interactive={false}
          />
        )}
      </Pane>

      {facilities.map((facility) => {
        const [lon, lat] = facility.geometry.coordinates
        const color = CATEGORY_COLORS[schoolCategory(facility.properties.facility_subtype)]
        const eligible = facility.properties.proximity_eligible
        const focused = focusedIds.has(facility.properties.id)
        return (
          <CircleMarker
            key={facility.properties.id}
            center={[lat, lon]}
            radius={focused ? 7 : 5}
            pathOptions={{
              color: eligible ? '#ffffff' : color,
              weight: eligible ? 1.5 : 2.5,
              opacity: focused ? 1 : 0.5,
              fillColor: color,
              fillOpacity: eligible ? (focused ? 0.95 : 0.35) : 0,
            }}
          >
            <Popup>
              <FacilityPopup facility={facility.properties} />
            </Popup>
          </CircleMarker>
        )
      })}

      {cities && <FitToCities cities={cities} selectionKey={selectionKey} />}
    </MapContainer>
  )
}
