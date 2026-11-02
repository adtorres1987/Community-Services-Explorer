# Architecture

```text
 CDE GeoJSON ─┐
              ├─ scripts/download_data.py ─► data/raw/ (not committed)
 TIGER/Line ──┘
                         │
                         ▼
              scripts/prepare_schools.py   filter, validate, reproject, flag
                         │
                         ▼
          data/processed/study_area.gpkg   (committed, EPSG:26911)
                         │
                         ▼
              scripts/load_postgis.py      (the `loader` service in Docker)
                         │
                         ▼
               PostgreSQL 17 + PostGIS 3.5
           facilities, city_boundaries (SRID 26911, GiST)
                         │  SQL: ST_Intersects, ST_DWithin, ST_Buffer, ST_Union
                         ▼
                 FastAPI  (backend/app)
           GeoJSON in EPSG:4326, coverage in metres
                         │  HTTP / JSON
                         ▼
          React + TypeScript + Leaflet  (frontend/src)
                         │
                         ▼
             nginx: static app + /api proxy  →  http://localhost:8080
```

## Components

| Layer | Location | Responsibility |
|---|---|---|
| Data pipeline | `scripts/` | Download and verify sources, build the study-area GeoPackage, load PostGIS |
| Database | `database/` | Schema migration and documented spatial queries |
| API | `backend/app/` | `api/` routes and validation, `services/` SQL, `schemas/` response models |
| Frontend | `frontend/src/` | Map, filters, statistics; typed API client |
| Runtime | `docker-compose.yml` | `db`, one-shot `loader`, `api`, `frontend` (nginx) |
| CI | `.github/workflows/ci.yml` | Python tests with PostGIS, frontend lint/tests/build, Compose smoke test |

## Key decisions

- **One projected CRS for analysis (EPSG:26911).** Distances and areas are in
  metres without geography casts; the API transforms to EPSG:4326 only for output.
  EPSG:3857 (the source CRS) overstates distance by ~21 % at this latitude.
- **Spatial work happens in PostGIS.** The API does not load geometries into
  Python to compute coverage; the database buffers, unions and clips in one query.
- **Generic `facilities` table.** Common columns plus a JSONB `attributes`
  column, so parks or libraries (roadmap Phase 7) fit without schema changes.
- **Flags instead of deletions.** Schools outside city limits and virtual
  schools stay in the data with `in_city_limits` / `proximity_eligible` flags,
  so every exclusion is visible and explainable.
- **Committed processed data.** The 160 KB GeoPackage is committed so the app
  runs from a clone even if the publishers update their datasets; the raw
  sources are reproducible with checksums.
- **Same-origin deployment.** nginx serves the built frontend and proxies
  `/api` to FastAPI, so the Docker stack needs no CORS configuration.
- **Explicit errors.** 404 for unknown cities or ids, 422 for invalid
  parameters, 503 when the database is down; the frontend shows each with a retry.
