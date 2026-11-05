# Architecture

```text
 CDE schools GeoJSON ───────┐
 TIGER/Line 2026 places ────┤
 TIGER/Line 2020 blocks ────┼─ scripts/download_data.py ─► data/raw/ (not committed)
 Census 2020 P.L. 94-171 ───┘
                         │
                         ▼
              scripts/prepare_study_area.py   assign by boundary, context schools,
                         │                    apportion block population
                         ▼
          data/processed/study_area.gpkg   (committed, ~3 MB, EPSG:26911)
                         │
                         ▼
              scripts/load_postgis.py      (the `loader` service in Docker)
                         │
                         ▼
               PostgreSQL 17 + PostGIS 3.5
     facilities, city_boundaries, population_units (SRID 26911, GiST)
                         │  SQL: ST_DWithin, ST_Buffer, ST_Union, ST_Intersection
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
| Database | `database/` | Schema migrations and documented spatial queries |
| API | `backend/app/` | `api/` routes and validation, `services/` SQL, `schemas/` response models |
| Frontend | `frontend/src/` | Map, filters, statistics; typed API client |
| Runtime | `docker-compose.yml` | `db`, one-shot `loader`, `api`, `frontend` (nginx) |
| CI | `.github/workflows/ci.yml` | Python tests with PostGIS, frontend lint/tests/build, Compose smoke test |

## Key decisions

- **One projected CRS for analysis (EPSG:26911).** Distances and areas are in
  metres without geography casts; the API transforms to EPSG:4326 only for output.
  EPSG:3857 (the source CRS) overstates distance by ~21 % at this latitude.
- **Spatial work happens in PostGIS.** The API does not load geometries into
  Python to compute coverage; the database buffers, unions, clips and sums
  population in one query.
- **Assignment by boundary, not address.** Schools belong to the place that
  contains them; mailing-address cities include neighbourhoods and typos.
- **No edge effect.** Schools up to 2 km outside the study area (the largest
  radius) are loaded as context so coverage near boundaries is complete.
- **Population as well as area.** Area coverage alone misleads where land is
  hills or open space; residents are estimated from 2020 census blocks.
- **Generic `facilities` table.** Common columns plus a JSONB `attributes`
  column, so parks or libraries (roadmap Phase 7) fit without schema changes.
- **Flags instead of deletions.** Context and virtual schools stay in the data
  with `in_study_area` / `proximity_eligible` flags, so every exclusion is
  visible and explainable.
- **Study places are configuration.** `STUDY_PLACES` in
  `scripts/prepare_study_area.py` lists TIGER/Line GEOIDs; the API and the
  frontend read the places from the database.
- **Committed processed data.** The ~3 MB GeoPackage is committed so the app
  and CI run from a clone without downloading ~100 MB of census files, and
  even if the publishers update their datasets; the raw sources are
  reproducible with checksums. Block geometry is simplified (1 m) to keep it small.
- **Same-origin deployment.** nginx serves the built frontend and proxies
  `/api` to FastAPI, so the Docker stack needs no CORS configuration.
- **Additive migrations.** Schema changes go in new numbered files
  (`002_…`), so an existing database can be upgraded without losing history.
- **Explicit errors.** 404 for unknown places or ids, 422 for invalid
  parameters, 503 when the database is down; the frontend shows each with a retry.
