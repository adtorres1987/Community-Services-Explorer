# Data sources

## California Public Schools 2025–26

| Item | Value |
|---|---|
| Publisher | California Department of Education (CDE) |
| Catalog page | https://data.ca.gov/@california-department-of-education/california-public-schools-2025-26 |
| Homepage | https://gis.data.ca.gov/datasets/CDEGIS::california-public-schools-2025-26 |
| Rights | No restrictions on public use |
| Public access level | Public |
| Contact | orrp@cde.ca.gov |
| Update frequency | Irregular |
| Created (catalog) | 2026-04-24 |
| Last updated (catalog) | 2026-10-28 |
| Download URL (GeoJSON) | https://gis.data.ca.gov/api/download/v1/items/0cab44bcfd9a44eb88197147e4d37e8b/geojson?layers=0 |
| Downloaded | 2026-11-02 |
| Local file | `data/raw/california-public-schools-2025-2026.geojson` (not committed) |
| SHA-256 | `29d5af3991a2151c4e13d72726322f85bd9d098c556c4a4b09cbc965693e68af` |

Both raw sources are downloaded and checksum-verified by
`python scripts/download_data.py` (see `data/README.md`). The raw GeoJSON is
the original and must not be modified. A GeoPackage exported from it in QGIS
during inspection has identical geometries but drops the `OBJECTID` column;
it is not used by the pipeline.

### Inspection results

Run with `python scripts/inspect_schools.py`.

- Records: 9,946 (9,944 `Active`, 2 `Closed`)
- Geometry: 9,946 `Point`; 0 null, 0 empty
- CRS: **EPSG:3857** (Web Mercator), declared in the GeoJSON `crs` member
- Geometry matches the `Latitude` / `Longitude` attributes
- `CDSCode` is unique (0 duplicates) — candidate for `source_id`
- `OpenDate` uses a non-standard ISO format (`2006-08-28T00:00:00.0Z`);
  pyogrio warns but parses it correctly

### Key fields

| Purpose | Field | Notes |
|---|---|---|
| Identifier | `CDSCode` | 14-digit County-District-School code, unique |
| Name | `SchoolName` | |
| City | `City` | Mailing-address city, **not** municipal boundary |
| Type | `SchoolType` | e.g. Elementary, Middle, High, K-12, Continuation |
| Level | `SchoolLevel` | |
| Status | `Status` | `Active` / `Closed` |
| Charter | `Charter` | `Y` / `N` |
| Virtual | `Virtual` | `N` not virtual, `C` primarily classroom, `F` primarily virtual, `V` exclusively virtual |
| District | `DistrictName` | Administering district (charters may belong to districts elsewhere) |
| Location | `geometry`, `Latitude`, `Longitude` | |

### Study area records (`City` = Redlands / Yucaipa)

| | Redlands | Yucaipa |
|---|---|---|
| Records (all `Active`) | 24 | 13 |
| Main district | Redlands Unified (19) | Yucaipa-Calimesa Joint Unified (13) |
| Charters from other districts | 5 | 0 |
| `Virtual = V` | 4 | 0 |
| `Virtual = F` | 0 | 1 |

### Data quality notes

- **`City` is an address attribute.** Redlands Unified also operates schools
  with Highland, Mentone and Loma Linda addresses, which this filter excludes.
  An address city does not guarantee the school is within city limits; see the
  comparison with TIGER/Line boundaries below.
- **Exclusively virtual schools are administrative locations.** The three
  Sage Oak Charter records share one point (1473 Ford St. Ste. #105, Redlands).
  Their location does not represent where students are served.
- Gorman Learning Center (two records, Gorman Joint and Lucerne Valley Unified)
  are charters administered by districts outside the study area with a
  Redlands address.

### Processing criteria (Phase 2)

- Filter: `City IN ('Redlands', 'Yucaipa')` and `Status = 'Active'`.
- Add `in_city_limits` (point within the TIGER/Line boundary of its address
  city). Records outside the limits are kept; see the comparison below.
- Keep `Virtual = 'V'` records but flag them and exclude them from proximity analysis.
- Working CRS: **EPSG:26911** (NAD83 / UTM zone 11N, metres). EPSG:3857 is not
  suitable for distance measurement (≈0.83 true metres per unit at 34°N).

Implemented in `scripts/prepare_schools.py`, which writes
`data/processed/study_area.gpkg` (EPSG:26911) with two layers:

| Layer | Features | Notes |
|---|---|---|
| `schools` | 37 | Selected source fields + `in_city_limits`, `proximity_eligible` |
| `city_boundaries` | 2 | Redlands and Yucaipa from TIGER/Line 2026 |

Record flow: 9,946 read → 9,909 excluded (`City`) → 0 excluded (`Status`) → 37 written.
35 are `in_city_limits`, 33 are `proximity_eligible`. The GeoPackage is
committed to the repository; `tests/test_processed_data.py` checks these counts.

## Municipal boundaries — TIGER/Line 2026 Places (California)

| Item | Value |
|---|---|
| Publisher | U.S. Census Bureau |
| URL | https://www2.census.gov/geo/tiger/TIGER2026/PLACE/tl_2026_06_place.zip |
| Rights | Public domain (U.S. Government work) |
| Server last-modified | 2026-10-06 |
| Downloaded | 2026-11-02 |
| Local file | `data/raw/tl_2026_06_place/` (not committed) |
| SHA-256 (zip) | `4f1475be8db892b1d4894011846c5c857fe445bf876e470003170cd333d68032` |

- 1,622 places, CRS **EPSG:4269** (NAD83 geographic)
- Redlands city: `GEOID` 0659962, 93.86 km²; Yucaipa city: `GEOID` 0687042, 73.13 km²
  (areas computed in EPSG:26911); both geometries valid
- Selection: `NAME IN ('Redlands', 'Yucaipa')` and `LSAD = '25'` (city)
- TIGER/Line boundaries are cartographic products for statistical use, not
  legal survey boundaries.

### Address city vs. city limits (active schools)

| `City` (address) | Inside Redlands | Inside Yucaipa | Outside both |
|---|---|---|---|
| Redlands | 22 | 0 | 2 |
| Yucaipa | 0 | 13 | 0 |

No school with another address city falls inside either boundary.

Outside city limits despite a Redlands address:

| School | Distance to Redlands boundary |
|---|---|
| Mission Elementary (10568 California St.) | 89 m |
| Redlands East Valley High (31000 East Colton Ave.) | 772 m |
