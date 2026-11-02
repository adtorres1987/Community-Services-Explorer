# API (FastAPI)

## Run

Requires the PostGIS container running and loaded (see `docs/database.md`).

```bash
source .venv/bin/activate
uvicorn app.main:app --app-dir backend --port 8010 --reload
```

- Interactive docs (OpenAPI): http://localhost:8010/docs
- Port 8010 is used because 8000 is taken by another local service.
- Settings come from `.env`; `CORS_ORIGINS` lists the frontend origins allowed to call the API.

## Endpoints

All geometries are GeoJSON in **EPSG:4326**. Distances are computed in EPSG:26911 (metres).

| Method | Endpoint | Parameters | Returns |
|---|---|---|---|
| GET | `/health` | — | API, database and PostGIS version; 503 if the database is unreachable |
| GET | `/facilities` | `city`, `facility_type`, `facility_subtype` (all optional) | FeatureCollection of facilities |
| GET | `/facilities/{id}` | `id` ≥ 1 | Feature |
| GET | `/cities` | — | FeatureCollection of city boundaries with area and facility count |
| GET | `/analysis/proximity` | `radius_m` (100–2000, required), `city`, `facility_type` | Coverage per city |

### `/analysis/proximity`

For each city, the share of the city area within `radius_m` of a
proximity-eligible facility whose address city is that city. The buffers are
clipped to the city boundary and returned as `coverage` geometry.

```json
{
  "radius_m": 1000,
  "facility_type": null,
  "method": "Straight-line (Euclidean) distance measured in EPSG:26911. ...",
  "results": [
    {
      "city": "Yucaipa",
      "city_area_km2": 73.13,
      "eligible_facilities": 13,
      "excluded_facilities": 0,
      "covered_area_km2": 25.36,
      "covered_pct": 34.7,
      "coverage": { "type": "MultiPolygon", "coordinates": [] }
    }
  ]
}
```

`excluded_facilities` counts records that are not proximity eligible
(exclusively virtual schools). A `facility_type` with no facilities returns
`eligible_facilities: 0`, `covered_pct: 0` and `coverage: null`.

## Errors

| Status | When |
|---|---|
| 404 | Unknown `city`, or facility `id` not found |
| 422 | Invalid parameters (e.g. `radius_m` outside 100–2000, non-numeric `id`) |
| 503 | Database unavailable (`{"detail": "Database unavailable"}`) |

## Tests

Integration tests run against the loaded PostGIS container:

```bash
python -m pytest
```

They check record counts, WGS84 coordinates, filters, error codes, and that
coverage percentages match the values verified independently with GeoPandas.
