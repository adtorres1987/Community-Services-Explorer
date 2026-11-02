# Database (PostGIS)

## Setup

```bash
cp .env.example .env              # then set POSTGRES_PASSWORD
docker compose up -d --wait db    # applies database/migrations on first start
python scripts/load_postgis.py    # loads data/processed/study_area.gpkg
```

`docker compose up -d --build` (the full stack) runs the same load in the
one-shot `loader` service.

- Image: `imresamu/postgis:17-3.5` (PostgreSQL 17, PostGIS 3.5). It is a
  multi-arch build of the official image; `postgis/postgis` has no arm64 build.
- Port: `127.0.0.1:5434` (5432 and 5433 were already in use locally).
- Migrations in `database/migrations/` run only when the data volume is empty.
  To recreate the database from scratch: `docker compose down -v`, then start again.
- `load_postgis.py` replaces the rows of each source inside one transaction
  and fails if the loaded row counts differ from the GeoPackage, so it can be re-run.

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
| `city` | `TEXT` | Address city |
| `in_city_limits` | `BOOLEAN` | Point within the address city's boundary |
| `proximity_eligible` | `BOOLEAN` | `false` for exclusively virtual schools |
| `attributes` | `JSONB` | Source-specific fields (level, grades, charter, district, address, website, enrolment) |
| `geom` | `geometry(Point, 26911)` | GiST index |

**`city_boundaries`** — `geoid`, `name`, `source_name`, `geom geometry(MultiPolygon, 26911)` with GiST index.

## Spatial queries

`database/sql/spatial_queries.sql` exercises `ST_Intersects`, `ST_DWithin`,
`ST_Buffer`, `ST_Distance` and `ST_Transform`. Run it with:

```bash
docker compose exec -T db sh -c 'psql -U "$POSTGRES_USER" -d "$POSTGRES_DB"' < database/sql/spatial_queries.sql
```

Verified results (2026-11-02):

- Both geometry columns report SRID 26911; both GiST indexes exist.
- `ST_Intersects` finds 22 schools in Redlands and 13 in Yucaipa, matching
  `in_city_limits`. Mission Elementary (89 m) and Redlands East Valley High
  (772 m) lie outside Redlands, matching the Phase 2 comparison.
- Projected (UTM) and geodesic distances agree to the metre at this scale.
- Share of city area within a radius of an eligible school:

| City | 500 m | 1 km |
|---|---|---|
| Redlands (93.86 km²) | 12.9 % | 38.8 % |
| Yucaipa (73.13 km²) | 11.1 % | 34.7 % |

  An independent GeoPandas calculation gives the same values within 0.1
  points (buffer segment approximation differs).

## Notes for the analysis

- **Co-located schools.** Gorman Learning Center and Gorman Learning Center
  San Bernardino/Santa Clarita are 1 m apart; Green Valley High and Green
  Valley Independent Study are 4 m apart. Counts of "schools within a radius"
  count each record, not each site.
- **Edge effect.** Only schools with a Redlands or Yucaipa address are loaded.
  Schools just outside the cities (Highland, Mentone, Loma Linda, Calimesa)
  are not, so coverage near city edges is underestimated.
- Radii are straight-line distances. They do not measure street access,
  capacity or enrolment boundaries.
