# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

Community Services Explorer: public schools, public libraries and transit stops in nine San Bernardino Valley communities (Colton, Grand Terrace, Highland, Loma Linda, Mentone CDP, Redlands, Rialto, San Bernardino, Yucaipa) and how many residents (all, and aged 5–17) and how much land lie within a straight-line radius of one. The app shows one service at a time. Pipeline: Python/GeoPandas → PostGIS → FastAPI → React + Leaflet. The project plan and status (Spanish) is `community-services-explorer-roadmap.md`; the user communicates in Spanish, code and docs are in English.

## Commands

Python 3.14 in `.venv` (`source .venv/bin/activate`); Node 24+ in `frontend/`.

```bash
# Database (PostGIS on 127.0.0.1:5434) and data load — needed by all Python tests
cp .env.example .env
docker compose up -d --wait db
python scripts/load_postgis.py

# API on :8010 (docs at /docs); frontend dev server on :5174
uvicorn app.main:app --app-dir backend --port 8010 --reload
cd frontend && npm run dev

# Tests
python -m pytest                                   # pipeline (tests/) + API (backend/tests/)
python -m pytest backend/tests/test_analysis.py -k Redlands   # single test
cd frontend && npm test                            # Vitest; single file: npx vitest run src/components/FilterPanel.test.tsx
cd frontend && npm run lint && npm run build       # oxlint; tsc -b + vite build

# Full stack (db + one-shot loader + api + nginx frontend) on :8080
docker compose up -d --build --wait

# Rebuild the committed dataset from original sources (~1.2 GB download, checksum-verified)
python scripts/download_data.py && python scripts/prepare_study_area.py && python scripts/load_postgis.py
```

`pytest.ini` puts `backend` and `scripts` on the path, so tests import `app.*` and `prepare_study_area` directly. The API tests are integration tests: if they all return 503, the db container is down.

Ports 5432, 5433, 8000 and 5173 are used by other local projects; this repo uses 5434, 8010, 5174 and 8080. CORS allows `localhost:5174` and `127.0.0.1:5174` by default (`CORS_ORIGINS`).

## Architecture

**Data flow.** `scripts/download_data.py` fetches sources into `data/raw/` (never committed, SHA-256 pinned; a mismatch means the publisher changed the file). `scripts/prepare_study_area.py` writes `data/processed/study_area.gpkg` (committed, ~3 MB, EPSG:26911) with layers `schools`, `libraries`, `transit_stops`, `city_boundaries`, `population_units`; each source has its own selection function and they share `assign_to_places` (boundary assignment + context facilities). `scripts/load_postgis.py` replaces rows per `source_name` in one transaction and fails on row-count mismatch. In Docker the `loader` service runs the same script.

**Spatial model — the non-obvious rules:**
- All analysis is in **EPSG:26911** (metres) inside PostGIS; the API emits GeoJSON in EPSG:4326. Source schools are EPSG:3857, which is not valid for distances.
- Facilities are assigned to a place **by boundary (spatial join), not by mailing-address city**. `facilities.city` is the containing study place; `address_city` keeps the source address. "Context" facilities (`in_study_area = false`, `city IS NULL`, enforced by a CHECK) lie within the largest radius offered for their service (2 km schools, 3.2 km libraries, 800 m transit) and only contribute to coverage. Raising a service's maximum radius means raising its context distance and the API's `radius_m` limit (3200) together.
- `proximity_eligible = false` for exclusively virtual schools (administrative addresses).
- Coverage = `ST_Union(ST_Buffer(...))` of all eligible facilities within the radius (including neighbouring places and context facilities), clipped to each boundary. Covered population = Σ block population × (covered area / block area). Blocks are 2020 census blocks clipped to 2026 boundaries; population is apportioned by area in the pipeline, and geometry is simplified (1 m) only *after* apportioning.
- Population sources: total from P.L. 94-171 (`cageo2020.pl`, block SUMLEV 750); ages 5–17 from DHC table P12 (segment 6 `ca000062020.dhc`, block SUMLEV **100**, joined on LOGRECNO). Both are exact at block level and must sum to the county totals.
- A school near a shared boundary contributes to several places: when combining places, count distinct `contributing_facility_ids`, never sum `contributing_facilities`. Population and area can be summed (weighted percentages).

**Backend (`backend/app`).** Routers in `api/` are thin; SQL lives in `services/` (raw psycopg 3, `dict_row`, pool on `app.state.pool` created in the lifespan). Pydantic models in `schemas/` define the response shapes and are mirrored by hand in `frontend/src/services/api.ts`; change both together. DB errors map to 503. The proximity query computes each block's covered share once in a `MATERIALIZED` CTE; without it PostgreSQL inlines the expression into each population sum and the query is ~50 % slower.

**Database.** `database/migrations/NNN_*.sql` are additive and run only on an empty volume (mounted into `docker-entrypoint-initdb.d`). Migrations after 001 are wrapped in BEGIN/COMMIT so they can be applied to an existing DB with `psql`, followed by a reload. New columns that the loader fills are nullable, and the API/frontend tolerate `null` until reload. `database/sql/spatial_queries.sql` holds documented, runnable verification queries.

**Frontend (`frontend/src`).** `App.tsx` owns filter state (service, selected communities — empty means all —, subtype, radius, population group). `useRequest` fetches with abort/retry; all facilities and cities load once and are filtered by service in the browser; proximity is re-requested per service/radius/subtype. `features/facilities/services.ts` is the service registry (labels, colours, radii, caveat, source per `facility_type`); service-specific helpers are in `schools.ts` / `libraries.ts`, selection logic in `filters.ts`, and combining per-place results (weighted totals, distinct contributors, population group) in `coverage.ts`. `MapView` uses panes for draw order, fractional zoom, and defers `fitBounds` while a zoom animation runs (Leaflet ignores it otherwise).

- Transit stops are classified in the pipeline from GTFS (AM-peak departures per hour on `TRANSIT_SERVICE_DATE`, a weekday inside both feeds' service periods) into `facility_subtype` (service level). GTFS sources are pinned to Mobility Database archive URLs because agency URLs change content with every schedule. A new schedule means updating the URL, checksum and service date together.

**Adding a service** (roadmap Phase 7: clinics, parks next): a download entry with checksum, a `select_<service>` function plus a GeoPackage layer, a block in `load_postgis.py` with its `facility_type` and attributes, an entry in `SERVICES`, popup fields in `FacilityPopup`, and independently verified test values. Without `facility_type`, `/analysis/proximity` mixes all types, so tests and clients must pass it. Points only so far; polygon services (parks) would need a schema change.

## Verification practice

Expected numbers in tests (school counts, populations, coverage %) were verified independently with GeoPandas from the GeoPackage; `docs/database.md` and `docs/data-sources.md` record them. When the data or the method changes, recompute independently and update the tests and those docs together. CI (`.github/workflows/ci.yml`) runs on push to `main` and on pull requests: Python tests against a loaded PostGIS, frontend lint/test/build, and a Docker Compose smoke test that checks plumbing only. README screenshots live in `docs/images/` (1280×800 @2x and 390×844 @2x).

## Working agreements

- Ask instead of assuming when a decision is the user's (data sources, scope, UI behaviour).
- Commit or push only when asked; features go on a branch with a PR. Never commit `.env` or `data/raw/`.
- Analysis limitations must stay explicit in the UI and in `docs/analysis-limitations.md` (straight-line distance, not access).
