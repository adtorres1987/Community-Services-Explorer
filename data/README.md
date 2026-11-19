# Data

| Path | Committed | Contents |
|---|---|---|
| `raw/` | No | Original downloads, never modified |
| `processed/study_area.gpkg` | Yes | Schools, libraries, transit stops, community boundaries and census population units (EPSG:26911), ~3 MB |

## Getting the raw data

```bash
python scripts/download_data.py
```

Downloads the eight sources into `raw/` (~1.2 GB) and verifies their SHA-256 checksums:

- `raw/california-public-schools-2025-2026.geojson` — CDE California Public
  Schools 2025–26 ("No restrictions on public use")
- `raw/tl_2026_06_place/` — Census TIGER/Line 2026 Places for California
- `raw/tl_2020_06071_tabblock20/` — Census TIGER/Line 2020 blocks, San Bernardino County
- `raw/ca2020.pl/` — Census 2020 P.L. 94-171 redistricting data for
  California; only the geographic header `cageo2020.pl` (block population) is extracted
- `raw/ca2020.dhc/` — Census 2020 Demographic and Housing Characteristics File for
  California (1.06 GB zip); only the geographic header `cageo2020.dhc` and segment
  `ca000062020.dhc` (table P12, sex by age) are extracted (~690 MB)
- `raw/pls_fy2024/` — IMLS Public Libraries Survey FY 2024 (20 MB zip); only the
  outlet and system CSV files are extracted
- `raw/gtfs/` — Omnitrans and Metrolink GTFS schedules (2 MB), archived copies
  from the Mobility Database; read straight from the zip files

The Census and IMLS files are public domain; the GTFS feeds are free downloads
from the agencies, which state no license (see `docs/data-sources.md`). A checksum mismatch means the publisher
changed the file. Review the change, update `docs/data-sources.md`, then
re-run with `--accept-changed`.

## Rebuilding the processed data

```bash
python scripts/prepare_study_area.py
```

The study communities are set by GEOID in `STUDY_PLACES` in that script.
Full source metadata, field descriptions and processing criteria are in
[`docs/data-sources.md`](../docs/data-sources.md).
