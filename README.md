# Community Services Explorer

[![CI](https://github.com/adtorres1987/Community-Services-Explorer/actions/workflows/ci.yml/badge.svg)](https://github.com/adtorres1987/Community-Services-Explorer/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

A geospatial web application for exploring public schools in **Redlands and
Yucaipa, California**, and how much of each city lies within a straight-line
radius of one. Built end to end, from raw public data to an interactive map:
Python data pipeline → PostGIS → FastAPI → React + Leaflet.

![Both cities with 1 km proximity coverage](docs/images/overview-1km.jpg)

## Features

- Map of 37 active public schools with city boundaries, colour-coded by school type
- Filters by city and school type; popups with district, grades, enrolment and instruction mode
- Proximity coverage at 500 m or 1 km, computed in PostGIS and drawn on the map
- Side-by-side statistics for both cities, with the method and its limits stated in the UI
- REST API returning GeoJSON, with OpenAPI docs and explicit error handling
- Reproducible data pipeline with checksummed sources, and tests at every layer

| City | Schools | Area within 500 m | Area within 1 km |
|---|---|---|---|
| Redlands (93.86 km²) | 24 (20 eligible) | 12.9 % | 38.8 % |
| Yucaipa (73.13 km²) | 13 | 11.1 % | 34.7 % |

*Straight-line distance over land area, not travel time or population. See
[analysis limitations](docs/analysis-limitations.md).*

<p>
  <img src="docs/images/redlands-500m-popup.jpg" alt="Redlands at 500 m with a school popup" width="68%">
  <img src="docs/images/mobile.jpg" alt="Mobile layout" width="24%">
</p>

## Quick start (Docker)

Requires Docker with Compose v2 (Docker Desktop on macOS/Windows).

```bash
git clone https://github.com/adtorres1987/Community-Services-Explorer.git
cd Community-Services-Explorer
cp .env.example .env            # optionally change POSTGRES_PASSWORD
docker compose up -d --build --wait
```

Open http://localhost:8080. API docs are at http://localhost:8080/api/docs.

This starts PostGIS, loads the committed dataset (`data/processed/study_area.gpkg`),
then starts the API and the frontend (served by nginx, which also proxies `/api`).
Ports are set in `.env` (`POSTGRES_PORT`, default 5434; `APP_PORT`, default 8080).
Stop with `docker compose down`; add `-v` to delete the database volume.

## Local development

Requires Python 3.14 and Node.js 24+ (the versions CI uses).

```bash
# Python environment
python3.14 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Database only, then load the data
cp .env.example .env
docker compose up -d --wait db
python scripts/load_postgis.py

# API on http://localhost:8010 (docs at /docs)
uvicorn app.main:app --app-dir backend --port 8010 --reload

# Frontend on http://localhost:5174 (in another terminal)
cd frontend
npm install
npm run dev
```

### Rebuilding the data from the original sources

```bash
python scripts/download_data.py    # CDE schools + Census TIGER/Line, checksum-verified
python scripts/prepare_schools.py  # filter, validate, reproject → data/processed/study_area.gpkg
python scripts/load_postgis.py
```

## Tests

```bash
python -m pytest                   # data pipeline + API (needs the loaded database)
cd frontend && npm test            # components, helpers, API client
```

CI runs both suites plus a Docker Compose smoke test on every push.

## Architecture

```text
CDE + Census data → Python/GeoPandas pipeline → PostGIS → FastAPI → React + Leaflet
```

All analysis runs in **EPSG:26911** (NAD83 / UTM zone 11N, metres) inside
PostGIS; the API returns GeoJSON in EPSG:4326. Details and design decisions are
in [docs/architecture.md](docs/architecture.md).

| Layer | Technology |
|---|---|
| Data processing | Python 3.14, GeoPandas, Shapely, Pyogrio, PyProj; QGIS for visual validation |
| Database | PostgreSQL 17 + PostGIS 3.5 |
| API | FastAPI, Pydantic, psycopg 3 |
| Frontend | React 19, TypeScript, Vite, Leaflet / React-Leaflet |
| Testing | pytest, Vitest, Testing Library |
| Runtime / CI | Docker Compose, nginx, GitHub Actions |

```text
backend/        FastAPI app (api/, schemas/, services/) and API tests
frontend/       React app (components/, features/, maps/, services/)
scripts/        download_data.py, prepare_schools.py, load_postgis.py
database/       migrations/ and documented spatial queries (sql/)
data/           raw/ (downloaded, not committed) and processed/ (committed)
tests/          data pipeline tests
docs/           architecture, data sources, database, API, limitations
```

## Data sources

| Dataset | Publisher | Terms |
|---|---|---|
| [California Public Schools 2025–26](https://data.ca.gov/@california-department-of-education/california-public-schools-2025-26) | California Department of Education | No restrictions on public use |
| [TIGER/Line 2026 Places, California](https://www2.census.gov/geo/tiger/TIGER2026/PLACE/) | U.S. Census Bureau | Public domain |
| Basemap tiles | © [OpenStreetMap](https://www.openstreetmap.org/copyright) contributors | ODbL; [tile usage policy](https://operations.osmfoundation.org/policies/tiles/) |

Field descriptions, checksums and processing criteria: [docs/data-sources.md](docs/data-sources.md).

## Documentation

- [Architecture and design decisions](docs/architecture.md)
- [Data sources and processing](docs/data-sources.md)
- [Database model and spatial queries](docs/database.md)
- [API reference](docs/api.md)
- [Analysis limitations](docs/analysis-limitations.md)
- [Original project plan (Spanish)](community-services-explorer-roadmap.md)

## Next steps

- More community services: parks, libraries, clinics, transit (the `facilities` table is already generic)
- Network-based accessibility: walking distance and service areas on the street network
- Population-weighted coverage using census blocks
- OGC services (WMS/WFS, OGC API Features) and an ArcGIS Maps SDK comparison

## License

Code is released under the [MIT License](LICENSE). Data remains under the terms of its publishers.
