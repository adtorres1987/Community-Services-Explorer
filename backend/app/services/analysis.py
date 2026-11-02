from psycopg import Connection

from app.schemas.analysis import CityProximity, ProximityResponse

METHOD = (
    "Straight-line (Euclidean) distance measured in EPSG:26911. Coverage is the share "
    "of the city area within the radius of a proximity-eligible facility with that city "
    "as its address. It does not measure street-network access, capacity, or enrolment "
    "boundaries."
)

PROXIMITY_SQL = """
WITH per_city AS (
    SELECT
        b.name AS city,
        b.geom AS boundary,
        count(f.id) FILTER (WHERE f.proximity_eligible) AS eligible_facilities,
        count(f.id) FILTER (WHERE NOT f.proximity_eligible) AS excluded_facilities,
        ST_Union(ST_Buffer(f.geom, %(radius_m)s::float8)) FILTER (WHERE f.proximity_eligible) AS buffers
    FROM city_boundaries b
    LEFT JOIN facilities f
        ON f.city = b.name
       AND (%(facility_type)s::text IS NULL OR f.facility_type = %(facility_type)s)
       AND (%(facility_subtype)s::text IS NULL OR f.facility_subtype = %(facility_subtype)s)
    WHERE (%(city)s::text IS NULL OR b.name = %(city)s)
    GROUP BY b.id
),
clipped AS (
    SELECT *, ST_CollectionExtract(ST_Intersection(boundary, buffers), 3) AS coverage
    FROM per_city
)
SELECT
    city,
    eligible_facilities,
    excluded_facilities,
    ST_Area(boundary) / 1e6 AS city_area_km2,
    coalesce(ST_Area(coverage), 0) / 1e6 AS covered_area_km2,
    ST_AsGeoJSON(ST_Transform(coverage, 4326), 6)::json AS coverage
FROM clipped
ORDER BY city
"""


def proximity(
    conn: Connection,
    city: str | None,
    radius_m: int,
    facility_type: str | None,
    facility_subtype: str | None,
) -> ProximityResponse:
    rows = conn.execute(
        PROXIMITY_SQL,
        {
            "city": city,
            "radius_m": radius_m,
            "facility_type": facility_type,
            "facility_subtype": facility_subtype,
        },
    ).fetchall()
    results = [
        CityProximity(
            city=row["city"],
            city_area_km2=round(row["city_area_km2"], 2),
            eligible_facilities=row["eligible_facilities"],
            excluded_facilities=row["excluded_facilities"],
            covered_area_km2=round(row["covered_area_km2"], 2),
            covered_pct=round(100 * row["covered_area_km2"] / row["city_area_km2"], 1),
            coverage=row["coverage"],
        )
        for row in rows
    ]
    return ProximityResponse(
        radius_m=radius_m,
        facility_type=facility_type,
        facility_subtype=facility_subtype,
        method=METHOD,
        results=results,
    )
