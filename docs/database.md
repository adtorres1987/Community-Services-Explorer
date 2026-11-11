# Database (PostGIS)

## Setup

```bash
cp .env.example .env              # optionally change POSTGRES_PASSWORD
docker compose up -d --wait db    # applies database/migrations on first start
python scripts/load_postgis.py    # loads data/processed/study_area.gpkg
```

`docker compose up -d --build` (the full stack) runs the same load in the
one-shot `loader` service.

- Image: `imresamu/postgis:17-3.5` (PostgreSQL 17, PostGIS 3.5). It is a
  multi-arch build of the official image; `postgis/postgis` has no arm64 build.
- Port: `127.0.0.1:5434` by default (`POSTGRES_PORT` in `.env`), to avoid
  clashing with a local PostgreSQL on 5432.
- Migrations in `database/migrations/` run in order, only when the data volume
  is empty. To recreate the database: `docker compose down -v`, then start again.
  To upgrade an existing database instead, run the new migration with `psql`
  (each migration after 001 is wrapped in a transaction), then reload the data.
- `load_postgis.py` replaces the rows of each source inside one transaction
  and fails if the loaded row counts differ from the GeoPackage, so it can be re-run.

| Migration | Change |
|---|---|
| `001_create_tables.sql` | `facilities` and `city_boundaries` (first MVP: Redlands and Yucaipa) |
| `002_study_places_population.sql` | Assignment by boundary (`city` nullable, `address_city`, `in_city_limits` → `in_study_area`), place type and population on boundaries, `population_units` table |
| `003_school_age_population.sql` | `population_5_17` (2020 DHC, ages 5–17) on `city_boundaries` and `population_units`; nullable until the data is reloaded |

## Data model

All geometries use **SRID 26911** (NAD83 / UTM zone 11N, metres). The API
transforms to EPSG:4326 for GeoJSON output.

**`facilities`** — one row per facility, generic across future service types.

| Column | Type | Notes |
|---|---|---|
| `id` | `BIGINT` identity | Internal id |
| `source_id` | `TEXT` | `CDSCode` for schools; unique with `source_name` |
| `source_name` | `TEXT` | `cde_public_schools_2025_26` |
| `name` | `TEXT` | |
| `facility_type` | `TEXT` | `school` |
| `facility_subtype` | `TEXT` | CDE `SchoolType` (Elementary, High, …) |
| `city` | `TEXT` | Study place whose boundary contains the facility; `NULL` for context facilities |
| `address_city` | `TEXT` | Mailing-address city from the source |
| `in_study_area` | `BOOLEAN` | `false` for context facilities (within 2 km, coverage only); `CHECK (in_study_area = (city IS NOT NULL))` |
| `proximity_eligible` | `BOOLEAN` | `false` for exclusively virtual schools |
| `attributes` | `JSONB` | Source-specific fields (level, grades, charter, district, address, county, website, enrolment) |
| `geom` | `geometry(Point, 26911)` | GiST index |

**`city_boundaries`** — one row per study place: `geoid`, `name`, `place_type`
(`city` or `CDP`), `population` (2020), `population_5_17` (2020 DHC), `source_name`,
`geom geometry(MultiPolygon, 26911)` with GiST index.

**`population_units`** — 2020 census blocks clipped to each place: `geoid20`,
`city` (references `city_boundaries.name`), `population` and `population_5_17`
(apportioned by area, fractional), `source_name`, `geom geometry(MultiPolygon, 26911)` with GiST index.

## Spatial queries

`database/sql/spatial_queries.sql` exercises `ST_Intersects`, `ST_DWithin`,
`ST_Buffer`, `ST_Union`, `ST_Intersection`, `ST_Distance` and `ST_Transform`.
Run it with:

```bash
docker compose exec -T db sh -c 'psql -U "$POSTGRES_USER" -d "$POSTGRES_DB"' < database/sql/spatial_queries.sql
```

Verified results (2026-11-02):

- All geometry columns report SRID 26911; all GiST indexes exist.
- `ST_Intersects` counts per boundary match the assigned `city` for all nine places.
- Context schools lie between 40 m and 2 km from the study area.
- Projected (UTM) and geodesic distances agree to the metre at this scale.
- Coverage (any eligible school, including neighbouring places and context schools):

| Place | Area 500 m | Area 1 km | Residents 500 m | Residents 1 km | Ages 5–17 500 m | Ages 5–17 1 km |
|---|---|---|---|---|---|---|
| Colton | 20.1 % | 52.9 % | 37.7 % | 84.8 % | 38.4 % | 85.5 % |
| Grand Terrace | 29.2 % | 76.0 % | 36.7 % | 90.4 % | 37.5 % | 91.7 % |
| Highland | 16.1 % | 41.4 % | 41.8 % | 83.5 % | 44.0 % | 86.8 % |
| Loma Linda | 6.5 % | 25.9 % | 10.1 % | 28.7 % | 11.8 % | 29.9 % |
| Mentone | 10.5 % | 30.1 % | 33.8 % | 68.9 % | 34.3 % | 71.2 % |
| Redlands | 13.0 % | 39.6 % | 24.2 % | 74.8 % | 24.5 % | 76.4 % |
| Rialto | 28.1 % | 65.7 % | 47.5 % | 94.9 % | 47.9 % | 95.1 % |
| San Bernardino | 26.1 % | 58.2 % | 45.2 % | 88.3 % | 46.5 % | 89.2 % |
| Yucaipa | 11.1 % | 35.3 % | 22.1 % | 59.4 % | 23.6 % | 61.6 % |

  An independent GeoPandas calculation from the GeoPackage (same buffer
  resolution) gives identical values for area, both populations (all four
  radii for ages 5–17, verified 2026-11-10) and the number of contributing
  schools.

## Performance

`/analysis/proximity` for all nine places runs in 0.4–0.7 s on a laptop
(buffer union, clip to boundaries, then area-weighted sums over ~6,800
population units using the GiST indexes); the response is 160–235 KB with
coverage geometry. The covered share of each block is computed once in a
`MATERIALIZED` CTE and reused for both populations; without it PostgreSQL
inlines the expression into each sum and the query is ~50 % slower.

See [analysis-limitations.md](analysis-limitations.md) for what these numbers
do and do not measure.
