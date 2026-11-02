# Frontend

React + TypeScript + Vite, with Leaflet / React-Leaflet for the map.

## Run

Requires the API on http://localhost:8010 (see `docs/api.md`).

```bash
npm install
npm run dev      # http://localhost:5174
npm run build    # type-check and production build
npm run lint     # oxlint
```

Set `VITE_API_URL` in `.env.local` to use another API address (see `.env.example`).
Port 5174 must be listed in the API's `CORS_ORIGINS`.

## Structure

```text
src/
├── components/   MapView, FilterPanel, StatisticsPanel, FacilityPopup, Legend
├── features/
│   └── facilities/schools.ts   school categories, colours, labels, filters
├── maps/basemap.ts             basemap and layer styles
├── services/
│   ├── api.ts                  typed API client (mirrors backend schemas)
│   └── useRequest.ts           fetch hook with abort, loading, error and retry
└── App.tsx                     filter state and layout
```

## Notes

- Facilities are loaded once and filtered in the browser (37 records). The
  proximity analysis is requested from the API for each radius / school type.
- Basemap: OpenStreetMap standard tiles, desaturated in CSS. They are for light
  use under the [OSM tile usage policy](https://operations.osmfoundation.org/policies/tiles/);
  a public deployment with real traffic should use a tile provider with a key.
- Marker colours use the Okabe–Ito palette. Exclusively virtual schools are
  drawn hollow because they are excluded from the proximity analysis.
