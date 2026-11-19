# Frontend

React + TypeScript + Vite, with Leaflet / React-Leaflet for the map.

## Run

Requires Node.js 24+ and the API on http://localhost:8010 (see `docs/api.md`).

```bash
npm install
npm run dev      # http://localhost:5174
npm test         # Vitest + Testing Library
npm run lint     # oxlint
npm run build    # type-check and production build
```

Set `VITE_API_URL` in `.env.local` to use another API address (see `.env.example`).
Port 5174 must be listed in the API's `CORS_ORIGINS` (it is the default).

In Docker (`docker compose up` from the repository root), the `Dockerfile`
builds the app with `VITE_API_URL=/api` and serves it with nginx, which proxies
`/api` to the API container (`nginx.conf`).

## Structure

```text
src/
├── components/   MapView, FilterPanel, StatisticsPanel, FacilityPopup, Legend
├── features/facilities/
│   ├── services.ts             service registry: labels, colours, radii, caveat per service
│   ├── schools.ts, libraries.ts  service-specific categories, colours and labels
│   ├── filters.ts              community / subtype selection and focus
│   └── coverage.ts             combines per-place results (weighted totals)
├── maps/basemap.ts             basemap and layer styles
├── services/
│   ├── api.ts                  typed API client (mirrors backend schemas)
│   └── useRequest.ts           fetch hook with abort, loading, error and retry
├── test/                       test setup and fixtures
└── App.tsx                     filter state and layout
```

Tests sit next to the code they cover (`*.test.ts`, `*.test.tsx`).

## Notes

- One service at a time ("Service": Schools / Libraries). Facilities of every
  type are loaded once (~225 records) and filtered in the browser; the
  proximity analysis is requested from the API for each service, radius and
  subtype. Each service has its own radii (`services.ts`); switching service
  keeps the coverage on at the new service's closest radius.
- To add a service: load it in the pipeline with a `facility_type`, add an
  entry to `SERVICES` and, if it has its own attributes, a section in
  `FacilityPopup`.
- One or several communities can be selected (no selection = all). The
  statistics table then lists only the selected communities with a weighted
  total, and one sentence summarizes the selection; contributing schools are
  counted once by id (`features/facilities/coverage.ts`).
- "Population" switches the statistics between all residents and residents
  aged 5–17; area and the map do not change. The option is disabled if the
  API returns no age data (database loaded before migration 003).
- Selecting communities highlights their facilities; facilities in other
  communities and context facilities stay on the map, faded, because they still
  count toward coverage. Facilities of other subtypes are hidden, since coverage
  uses only the selected subtype.
- Basemap: OpenStreetMap standard tiles, desaturated in CSS. They are for light
  use under the [OSM tile usage policy](https://operations.osmfoundation.org/policies/tiles/);
  a public deployment with real traffic should use a tile provider with a key.
- Marker colours use the Okabe–Ito palette. Exclusively virtual schools are
  drawn hollow because they are excluded from the proximity analysis.
- The map uses fractional zoom (`zoomSnap` 0.25) so the study area fills
  narrow mobile screens.
