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

## 2020 Census ages 5–17 — DHC table P12

| Item | Value |
|---|---|
| Publisher | U.S. Census Bureau |
| Dataset | 2020 Census Demographic and Housing Characteristics File (DHC), California |
| URL | https://www2.census.gov/programs-surveys/decennial/2020/data/demographic-and-housing-characteristics-file/California/ca2020.dhc.zip |
| SHA-256 (zip) | `380711a2de1313fea48f2184810baccc83e36643f145daab4a2f37130d815c61` (1,057,231,771 bytes) |
| Rights | Public domain (U.S. Government work) |
| Downloaded | 2026-11-10 |
| Local files | `data/raw/ca2020.dhc/` (not committed) |

- Table **P12 (Sex by age for selected age categories)** is published down to
  the block. Ages 5–17 = cells 4–6 (male 5–9, 10–14, 15–17) + cells 28–30
  (female). The table is in data segment 6 (`ca000062020.dhc`), after P10
  (71 cells) and P11 (73), per the Census `table_segments_dhc.csv`; only that
  segment and the geographic header `cageo2020.dhc` are extracted.
- DHC block records are `SUMLEV = 100` (not 750 as in P.L. 94-171) and join
  to the data segment on `LOGRECNO`.
- Checks: every P12 block record is internally consistent (total = male +
  female, each the sum of its age groups); the 35,839 blocks sum to
  **417,313** residents aged 5–17, equal to the DHC county record; and the
  DHC block totals (`POP100`) equal the P.L. 94-171 totals for every block.
- **Why DHC, not the ACS:** DHC counts are by block, so they use the same
  area apportionment as the total population, and have no sampling error.
  ACS 5-year estimates are more recent but only reach block groups and carry
  margins of error.
- **Disclosure avoidance.** 2020 Census counts below the state level include
  statistical noise (differential privacy). Block-level age counts are noisy
  individually; the Census Bureau recommends aggregating them, which the
  analysis does (thousands of blocks per community). Totals by block are
  not affected beyond what P.L. 94-171 already includes.

## Public Libraries Survey FY 2024 — library outlets

| Item | Value |
|---|---|
| Publisher | Institute of Museum and Library Services (IMLS) |
| Page | https://www.imls.gov/research-evaluation/surveys/public-libraries-survey-pls |
| Download URL (CSV) | https://www.imls.gov/sites/default/files/2026-06/pls_fy2024_csv.zip |
| SHA-256 (zip) | `73910b723f23d5ab6a45d472195621d5733a26c79e089494ae1e45f908bbbb8c` (20,133,862 bytes) |
| Documentation | FY 2024 Data Documentation and User's Guide (imls.gov, June 2026) |
| Rights | Public domain (U.S. Government work; public-use data files) |
| Downloaded | 2026-11-18 |
| Local files | `data/raw/pls_fy2024/` (not committed) |

- Two files are used: the **outlet file** (`pls_fy24_outlet_pud24i.csv`,
  17,615 outlets with geocoded `LATITUDE`/`LONGITUD`, WGS84) and the **system
  file** (`PLS_FY24_AE_pud24i.csv`, administrative entities), joined on
  `FSCSKEY` for the library system name.
- Fiscal year 2024 data, published in June 2026: openings, closures or moves
  since then are not reflected.
- **County law libraries are not public libraries.** California reports its 35
  county law libraries to the survey with `C_FSCS = N` (they do not meet the
  FSCS public library definition), e.g. the Law Library for San Bernardino
  County in downtown San Bernardino. They are excluded.

## Transit schedules — Omnitrans and Metrolink GTFS

| Item | Omnitrans | Metrolink |
|---|---|---|
| Publisher | Omnitrans | Southern California Regional Rail Authority (Metrolink) |
| Agency URL | http://www.omnitrans.org/google/google_transit.zip | https://metrolinktrains.com/globalassets/about/gtfs/gtfs.zip |
| Archived copy used | https://files.mobilitydatabase.org/mdb-97/mdb-97-202608140125/mdb-97-202608140125.zip | https://files.mobilitydatabase.org/mdb-96/mdb-96-202605230122/mdb-96-202605230122.zip |
| SHA-256 (zip) | `3ceca513d0e5f640ab2f1f5157184de13a6c9269273f8292e8fad887d4ac145a` | `d793a08b962f168f33c0e108bc41bf61b9b619b6e4ef72289a9828a28d97932b` |
| Feed version | `20260810_20260710a`, service 2026-08-10 to 2027-01-03 | `20260505`, service from 2026-05-05 |
| Terms | Free download; the agency says it provides data "under certain terms and conditions" but does not list them | Free download, no registration for the static feed; no license or terms stated |
| Downloaded | 2026-11-18 | 2026-11-18 |
| Local files | `data/raw/gtfs/` (not committed; read straight from the zips) | |

- **Terms.** Neither agency publishes a license for its static GTFS feed
  (checked 2026-11-18). The app uses stop locations and schedule counts derived
  from the feeds, with attribution; for wider redistribution, ask the agencies
  (Omnitrans: planning@omnitrans.org).
- **Why archived copies.** Agency URLs always serve the current schedule, so
  their content (and checksum) changes with every service change. The
  [Mobility Database](https://mobilitydatabase.org/) keeps each version at a
  fixed URL. The Omnitrans copy is byte-identical to the agency file of
  2026-11-18; the Metrolink copy has the same feed version as the agency file
  but was repackaged by Metrolink after the archive was made.
- **Omnitrans** runs 17 fixed routes in the study area, including the sbX Green
  Line (bus rapid transit). OmniRide (route type 715) is demand-responsive with
  no fixed stops and is excluded. Parent stations (`location_type = 1`) are
  dropped; their boarding platforms are kept.
- **Metrolink** includes the Arrow service to Redlands within the San
  Bernardino Line; 7 stations are in the study area.

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

**Libraries**

5. Keep California outlets with `C_FSCS = 'Y'` (public library systems; excludes
   the county law libraries), outlet type `CE` (central) or `BR` (branch;
   bookmobiles `BS` and books-by-mail `BM` have no fixed location), and not
   temporarily closed (`STATSTRU <> '23'`).
6. Assign by boundary like schools, and keep **context libraries** within
   3.2 km (2 miles, the largest radius offered for libraries) of the study area.
   All libraries are proximity eligible.
7. Upper-case PLS text is converted for display ("656 N. 9TH ST." →
   "656 N. 9th St."); negative PLS codes for missing numbers (−1, −3, −9)
   become empty.

**Transit stops**

8. Weekday service on a reference date, **Wednesday 16 September 2026** (inside
   both feeds' service periods, no holiday), from `calendar` and
   `calendar_dates`. Departures count trips that pick up passengers
   (`pickup_type` ≠ 1), all routes and directions at the stop.
9. Service level from AM-peak departures per hour (07:00–08:59): **Frequent
   bus** 4 or more (every 15 min or better), **every 20–30 min** 2 to 3.5,
   **less often** under 2; Metrolink stations are **Rail**. Stops with no
   departures on the reference date are kept but not proximity eligible.
10. Assign by boundary, and keep context stops within 800 m (½ mile, the
    largest radius offered for transit).

**Population**

11. Clip 2020 blocks to the study places. A block split by a boundary gets
   population in proportion to the area on each side (2020 blocks do not nest
   exactly in 2026 boundaries; 344 blocks are split).
12. Ages 5–17 (DHC) are apportioned the same way, block by block.
13. Simplify the clipped blocks with a 1 m tolerance *after* computing
   population, to keep the committed file small (~0.003 % area change).

**Working CRS:** EPSG:26911 (NAD83 / UTM zone 11N, metres). EPSG:3857 is not
suitable for distance measurement (≈0.83 true metres per unit at 34°N).

### Result

| Layer | Features | Notes |
|---|---|---|
| `schools` | 205 | 173 in the study area + 32 context; 7 not proximity eligible |
| `libraries` | 20 | 14 in the study area + 6 context |
| `transit_stops` | 1,249 | 1,162 in the study area (1,155 bus stops, 7 rail stations) + 87 context bus stops |

Transit stops in the study area by service level: frequent bus 238, every
20–30 min 445, less often 472, rail 7. By place: San Bernardino 554, Rialto
197, Redlands 99, Colton 93, Highland 71, Yucaipa 60, Loma Linda 55, Mentone
20, Grand Terrace 13.
| `city_boundaries` | 9 | With 2020 `population` and `population_5_17` |
| `population_units` | 6,839 | 6,487 blocks clipped to places, apportioned `population` and `population_5_17` |

| Place | Schools | Libraries | Population (2020) | Ages 5–17 (2020) |
|---|---|---|---|---|
| Colton | 15 | 2 | 53,915 | 10,689 |
| Grand Terrace | 4 | 1 | 13,148 | 2,129 |
| Highland | 10 | 1 | 56,969 | 11,893 |
| Loma Linda | 2 | 1 | 24,939 | 3,550 |
| Mentone | 2 | 1 | 9,557 | 1,712 |
| Redlands | 22 | 1 | 73,161 | 12,118 |
| Rialto | 28 | 2 | 104,063 | 21,785 |
| San Bernardino | 77 | 4 | 222,042 | 46,869 |
| Yucaipa | 13 | 1 | 54,541 | 9,724 |
| **Total** | **173** | **14** | **612,335** | **120,469** |

Libraries by system: San Bernardino County Library 8 (Grand Terrace,
Highland, Loma Linda, Mentone, Rialto 2, Yucaipa), San Bernardino Public
Library 4 (central Norman F. Feldheym and 3 branches), Colton Public Library 2
(central and Luque branch), A. K. Smiley Public Library 1 (Redlands, central).
Context libraries: Fontana Lewis, Summit (Fontana), Bloomington and Muscoy
(San Bernardino County Library), Highgrove and Calimesa (Riverside County
Library System).

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
- **Library names are truncated in the source** at 60 characters: "Highland Sam
  J. Racadio Library and Environmental Learning C[enter]".
- **Population is from 2020**, boundaries from 2026, schools from 2025–26 and
  libraries from fiscal year 2024, transit schedules from autumn 2026.

## Earlier scope (Redlands and Yucaipa)

The first MVP selected schools by address city (`City IN ('Redlands', 'Yucaipa')`)
and flagged two Redlands-address schools outside the city limits. With more
places the address city stopped being reliable (53 distinct values in the
county, including neighbourhoods and typos), so assignment moved to boundaries.
