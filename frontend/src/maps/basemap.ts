import type { LatLngExpression, PathOptions } from 'leaflet'

// OpenStreetMap standard tiles, desaturated in CSS (.map .leaflet-tile-pane) so the
// data layers stand out. Light use only: https://operations.osmfoundation.org/policies/tiles/
export const BASEMAP = {
  url: 'https://tile.openstreetmap.org/{z}/{x}/{y}.png',
  attribution:
    '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
  maxZoom: 19,
}

// Between Redlands and Yucaipa; replaced by the city bounds once loaded
export const INITIAL_CENTER: LatLngExpression = [34.045, -117.11]
export const INITIAL_ZOOM = 12

export const BOUNDARY_STYLE: PathOptions = {
  color: '#3d3d3d',
  weight: 2,
  dashArray: '6 4',
  fill: false,
}

export const COVERAGE_STYLE: PathOptions = {
  color: '#D55E00',
  weight: 1,
  fillColor: '#D55E00',
  fillOpacity: 0.18,
}
