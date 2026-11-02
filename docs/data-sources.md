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
| Downloaded | 2026-11-02 (GeoJSON resource) |
| Local file | `data/raw/california-public-schools-2025-2026.geojson` (not committed) |
| SHA-256 | `29d5af3991a2151c4e13d72726322f85bd9d098c556c4a4b09cbc965693e68af` |

The raw GeoJSON is the original and must not be modified. A GeoPackage copy
exported from QGIS (`data/raw/california_schools_2025_26.gpkg`) has identical
geometries but drops the `OBJECTID` column; it is a convenience copy, not the source.

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
  A Yucaipa address may fall outside city limits. Validate against municipal
  boundaries once a boundary source is chosen.
- **Exclusively virtual schools are administrative locations.** The three
  Sage Oak Charter records share one point (1473 Ford St. Ste. #105, Redlands).
  Their location does not represent where students are served.
- Gorman Learning Center (two records, Gorman Joint and Lucerne Valley Unified)
  are charters administered by districts outside the study area with a
  Redlands address.

### Proposed processing criteria (Phase 2)

- Filter: `City IN ('Redlands', 'Yucaipa')` and `Status = 'Active'`.
- Keep `Virtual = 'V'` records but flag them and exclude them from proximity analysis.
- Working CRS: **EPSG:26911** (NAD83 / UTM zone 11N, metres). EPSG:3857 is not
  suitable for distance measurement (≈0.83 true metres per unit at 34°N).

## Pending sources

- Municipal boundaries for Redlands and Yucaipa (not yet selected).
