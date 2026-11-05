# Data sources

Study area: nine contiguous communities in the San Bernardino Valley —
Colton, Grand Terrace, Highland, Loma Linda, Mentone, Redlands, Rialto,
San Bernardino and Yucaipa. Mentone is an unincorporated census-designated
place (CDP); the others are incorporated cities.

All raw sources are downloaded and checksum-verified by
`python scripts/download_data.py` (see `data/README.md`) and never modified.

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

A GeoPackage exported from the GeoJSON in QGIS during inspection has identical
geometries but drops the `OBJECTID` column; it is not used by the pipeline.

### Inspection results

Run with `python scripts/inspect_schools.py`.

- Records: 9,946 (9,944 `Active`, 2 `Closed`), statewide
- Geometry: 9,946 `Point`; 0 null, 0 empty
- CRS: **EPSG:3857** (Web Mercator), declared in the GeoJSON `crs` member
- Geometry matches the `Latitude` / `Longitude` attributes
- `CDSCode` is unique (0 duplicates) — used as `source_id`
- `OpenDate` uses a non-standard ISO format (`2006-08-28T00:00:00.0Z`);
  pyogrio warns but parses it correctly

### Key fields

| Purpose | Field | Notes |
|---|---|---|
| Identifier | `CDSCode` | 14-digit County-District-School code, unique |
| Name | `SchoolName` | |
| Address city | `City` | Mailing-address city: includes neighbourhood names and typos; **not** used to assign schools |
| Type | `SchoolType` | e.g. Elementary, Middle, High, K-12, Continuation |
| Level | `SchoolLevel` | |
| Status | `Status` | `Active` / `Closed` |
| Charter | `Charter` | `Y` / `N` |
| Virtual | `Virtual` | `N` not virtual, `C` primarily classroom, `F` primarily virtual, `V` exclusively virtual |
| District | `DistrictName` | Administering district (charters may belong to districts elsewhere) |
| County | `CountyNameGeo` | County where the school is located |
| Location | `geometry`, `Latitude`, `Longitude` | |

## TIGER/Line 2026 Places (California) — community boundaries

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
- Selected by `GEOID` (not name), see `STUDY_PLACES` in `scripts/prepare_study_area.py`:

| Place | GEOID | Type | Area (km², EPSG:26911) |
|---|---|---|---|
| Colton | 0614890 | city | 41.60 |
| Grand Terrace | 0630658 | city | 9.07 |
| Highland | 0633588 | city | 48.34 |
| Loma Linda | 0642370 | city | 23.20 |
| Mentone | 0646884 | CDP | 15.85 |
| Redlands | 0659962 | city | 93.86 |
| Rialto | 0660466 | city | 62.39 |
| San Bernardino | 0665000 | city | 163.09 |
| Yucaipa | 0687042 | city | 73.13 |

TIGER/Line boundaries are cartographic products for statistical use, not
legal survey boundaries. CDP boundaries are statistical, not administrative.

## 2020 Census population — blocks and P.L. 94-171

| Item | Value |
|---|---|
| Publisher | U.S. Census Bureau |
| Block geometry | https://www2.census.gov/geo/tiger/TIGER2020PL/LAYER/TABBLOCK/2020/tl_2020_06071_tabblock20.zip |
| SHA-256 (zip) | `46bdeb50e3d035b3268d908b0107b48123531375c9f422d6eca74b804af809f7` |
| Population counts | https://www2.census.gov/programs-surveys/decennial/2020/data/01-Redistricting_File--PL_94-171/California/ca2020.pl.zip |
| SHA-256 (zip) | `e02c83c85a9a5d69ded4bf0d4c8ebe3f4bcd2d8e5911db765e9e42915ad1f753` |
| Rights | Public domain (U.S. Government work) |
| Downloaded | 2026-11-02 |
| Local files | `data/raw/tl_2020_06071_tabblock20/`, `data/raw/ca2020.pl/` (not committed) |

- The block file (San Bernardino County, 35,839 blocks, EPSG:4269) has no
  population field. Counts come from the P.L. 94-171 geographic header
  `cageo2020.pl`, which carries `POP100` (total population) for every
  geography: block records are `SUMLEV = 750`, joined on `GEOCODE` = `GEOID20`.
  Only that file is extracted from the zip.
- Check: the 35,839 county blocks sum to **2,181,654**, the official 2020
  population of San Bernardino County, and every block geometry has a count.
- The Census API now requires a key; the bulk files do not.

## Processing (`scripts/prepare_study_area.py`)

Writes `data/processed/study_area.gpkg` (EPSG:26911), committed to the repository.

**Schools**

1. Keep `Status = 'Active'` schools statewide (2 closed records excluded).
2. Assign each school to the study place whose **boundary contains it**
   (spatial join) → `study_city`, `in_study_area = true`. The address city
   stays in `City`.
3. Also keep **context schools**: active schools outside the study area but
   within 2 km (the largest radius offered) of it, in any county. They count
   toward proximity coverage but not toward school counts
   (`in_study_area = false`, `study_city` empty).
4. `proximity_eligible = false` for exclusively virtual schools (`Virtual = 'V'`).

**Population**

5. Clip 2020 blocks to the study places. A block split by a boundary gets
   population in proportion to the area on each side (2020 blocks do not nest
   exactly in 2026 boundaries; 344 blocks are split).
6. Simplify the clipped blocks with a 1 m tolerance *after* computing
   population, to keep the committed file small (~0.003 % area change).

**Working CRS:** EPSG:26911 (NAD83 / UTM zone 11N, metres). EPSG:3857 is not
suitable for distance measurement (≈0.83 true metres per unit at 34°N).

### Result

| Layer | Features | Notes |
|---|---|---|
| `schools` | 205 | 173 in the study area + 32 context; 7 not proximity eligible |
| `city_boundaries` | 9 | With 2020 `population` |
| `population_units` | 6,839 | 6,487 blocks clipped to places, apportioned `population` |

| Place | Schools | Population (2020) |
|---|---|---|
| Colton | 15 | 53,915 |
| Grand Terrace | 4 | 13,148 |
| Highland | 10 | 56,969 |
| Loma Linda | 2 | 24,939 |
| Mentone | 2 | 9,557 |
| Redlands | 22 | 73,161 |
| Rialto | 28 | 104,063 |
| San Bernardino | 77 | 222,042 |
| Yucaipa | 13 | 54,541 |
| **Total** | **173** | **612,335** |

Context schools by address city: Fontana 16, San Bernardino (unincorporated) 8,
Bloomington 5, Riverside 2, Calimesa 1 (29 in San Bernardino County, 3 in
Riverside County). `tests/test_processed_data.py` checks these values.

### Data quality notes

- **Address city ≠ location.** 15 study-area schools have an address city
  different from the place that contains them, e.g. 6 "Highland" addresses
  inside San Bernardino, Mission Elementary ("Redlands") inside Loma Linda,
  Redlands East Valley High ("Redlands") inside Mentone. Assigning by boundary
  avoids this; the address is still shown in the app.
- **Exclusively virtual schools are administrative locations** (7: Redlands 4,
  Colton 1, Rialto 1, San Bernardino 1). The three Sage Oak Charter records
  share one point (1473 Ford St. Ste. #105, Redlands).
- **Co-located records.** Some schools share a site (distance 0–4 m): Del
  Vallejo Middle / Alternative Learning Center, Entrepreneur High / New Vision
  Middle, the two Gorman Learning Center records. Counts are of records.
- **Population is from 2020**, boundaries from 2026 and schools from 2025–26.

## Earlier scope (Redlands and Yucaipa)

The first MVP selected schools by address city (`City IN ('Redlands', 'Yucaipa')`)
and flagged two Redlands-address schools outside the city limits. With more
places the address city stopped being reliable (53 distinct values in the
county, including neighbourhoods and typos), so assignment moved to boundaries.
