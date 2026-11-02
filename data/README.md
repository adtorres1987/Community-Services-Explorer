# Data

| Path | Committed | Contents |
|---|---|---|
| `raw/` | No | Original downloads, never modified |
| `processed/study_area.gpkg` | Yes | Study-area schools and city boundaries (EPSG:26911), ~160 KB |

## Getting the raw data

```bash
python scripts/download_data.py
```

Downloads both sources into `raw/` and verifies their SHA-256 checksums:

- `raw/california-public-schools-2025-2026.geojson` — CDE California Public
  Schools 2025–26 ("No restrictions on public use")
- `raw/tl_2026_06_place/` — Census TIGER/Line 2026 Places for California
  (public domain)

A checksum mismatch means the publisher changed the file. Review the change,
update `docs/data-sources.md`, then re-run with `--accept-changed`.

## Rebuilding the processed data

```bash
python scripts/prepare_schools.py
```

Full source metadata, field descriptions and processing criteria are in
[`docs/data-sources.md`](../docs/data-sources.md).
