# API (FastAPI)

## Run

Requires the PostGIS container running and loaded (see `docs/database.md`).

```bash
source .venv/bin/activate
uvicorn app.main:app --app-dir backend --port 8010 --reload
```

- Interactive docs (OpenAPI): http://localhost:8010/docs
- Settings come from `.env`. `CORS_ORIGINS` lists the frontend origins allowed
  to call the API (default `http://localhost:5174`, the Vite dev server).

In the Docker stack the API is not published directly: nginx serves it at
http://localhost:8080/api (docs at http://localhost:8080/api/docs).

## Endpoints

All geometries are GeoJSON in **EPSG:4326**. Distances are computed in EPSG:26911 (metres).

| Method | Endpoint | Parameters | Returns |
|---|---|---|---|
| GET | `/health` | — | API, database and PostGIS version; 503 if the database is unreachable |
| GET | `/facilities` | `city`, `facility_type`, `facility_subtype` (all optional) | FeatureCollection of facilities, including context facilities |
| GET | `/facilities/{id}` | `id` ≥ 1 | Feature |
| GET | `/cities` | — | FeatureCollection of the nine study places with type, area, 2020 population and facility count |
| GET | `/analysis/proximity` | `radius_m` (100–2000, required), `city`, `facility_type`, `facility_subtype` | Coverage per place, by area and population |

The API keeps the name `city` for a study place; Mentone is a CDP, not a city.

### `/facilities`

`city` is the study place whose boundary contains the facility, and the `city`
filter uses it. `address_city` is the mailing address from the source and can
differ. Context facilities (`in_study_area: false`, `city: null`) are within
2 km of the study area and only contribute to coverage.

```json
{
  "id": 291,
  "name": "Redlands East Valley High",
  "facility_type": "school",
  "facility_subtype": "High",
  "city": "Mentone",
  "address_city": "Redlands",
  "in_study_area": true,
  "proximity_eligible": true,
  "attributes": { "GradeLow": "09", "GradeHigh": "12", "DistrictName": "Redlands Unified", "...": "..." }
}
```

### `/analysis/proximity`

For each place: the part of its area within `radius_m` of **any**
proximity-eligible facility (including facilities in neighbouring places and
context facilities), clipped to the boundary and returned as `coverage`
geometry; and the share of its 2020 residents in that area, apportioning each
census block's population by the share of its area covered.

```json
{
  "radius_m": 1000,
  "facility_type": null,
  "facility_subtype": null,
  "method": "Straight-line (Euclidean) distance measured in EPSG:26911. ...",
  "results": [
    {
      "city": "Yucaipa",
      "eligible_facilities": 13,
      "excluded_facilities": 0,
      "contributing_facilities": 15,
      "contributing_facility_ids": [301, 302, "..."],
      "city_area_km2": 73.13,
      "covered_area_km2": 25.82,
      "covered_pct": 35.3,
      "population": 54541,
      "covered_population": 32395,
      "covered_population_pct": 59.4,
      "coverage": { "type": "MultiPolygon", "coordinates": [] }
    }
  ]
}
```

- `eligible_facilities`: eligible facilities inside the place.
- `excluded_facilities`: facilities inside the place that are not eligible
  (exclusively virtual schools).
- `contributing_facilities`: eligible facilities anywhere within `radius_m`
  of the place (here 13 in Yucaipa plus 2 nearby).
- `contributing_facility_ids`: their ids. A school near a shared boundary
  contributes to both places, so to combine several places count the
  **distinct** ids rather than summing `contributing_facilities` (e.g. Colton
  and Rialto at 1 km: 62 distinct schools, 67 if summed). Population and area
  can be summed directly to get weighted percentages.
- A `facility_type` with no facilities returns zeros and `coverage: null`.
- All nine places take 0.6–0.8 s; pass `city` for a single place.

## Errors

| Status | When |
|---|---|
| 404 | Unknown `city`, or facility `id` not found |
| 422 | Invalid parameters (e.g. `radius_m` outside 100–2000, non-numeric `id`) |
| 503 | Database unavailable (`{"detail": "Database unavailable"}`) |

## Tests

Integration tests run against the loaded PostGIS container:

```bash
python -m pytest backend/tests
```

They check record counts, boundary-based assignment, WGS84 coordinates,
filters, error codes, and that area and population coverage match the values
verified independently with GeoPandas.
