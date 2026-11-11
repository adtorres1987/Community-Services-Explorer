from psycopg import Connection

from app.schemas.analysis import CityProximity, ProximityResponse

METHOD = (
    "Straight-line (Euclidean) distance measured in EPSG:26911. Coverage is the part of "
    "each study place within the radius of any proximity-eligible facility, including "
    "facilities in neighbouring places. Covered population apportions 2020 census block "
    "population (total, and aged 5-17 from the DHC) by area, assuming uniform density "
    "within each block. It does not measure street-network access, capacity, or "
    "enrolment boundaries."
)

PROXIMITY_SQL = """
WITH eligible AS (
    SELECT id, city, geom
    FROM facilities
    WHERE proximity_eligible
      AND (%(facility_type)s::text IS NULL OR facility_type = %(facility_type)s)
      AND (%(facility_subtype)s::text IS NULL OR facility_subtype = %(facility_subtype)s)
),
per_city AS (
    SELECT
        b.id,
        b.name AS city,
        b.geom AS boundary,
        b.population,
        b.population_5_17,
        (SELECT count(*) FROM eligible e WHERE e.city = b.name) AS eligible_facilities,
        (
            SELECT count(*)
            FROM facilities f
            WHERE f.city = b.name
              AND NOT f.proximity_eligible
              AND (%(facility_type)s::text IS NULL OR f.facility_type = %(facility_type)s)
              AND (%(facility_subtype)s::text IS NULL OR f.facility_subtype = %(facility_subtype)s)
        ) AS excluded_facilities,
        count(e.id) AS contributing_facilities,
        coalesce(array_agg(e.id ORDER BY e.id) FILTER (WHERE e.id IS NOT NULL), '{}')
            AS contributing_facility_ids,
        ST_Union(ST_Buffer(e.geom, %(radius_m)s::float8)) AS buffers
    FROM city_boundaries b
    -- Any eligible facility within the radius covers part of the place, wherever it is
    LEFT JOIN eligible e ON ST_DWithin(e.geom, b.geom, %(radius_m)s::float8)
    WHERE (%(city)s::text IS NULL OR b.name = %(city)s)
    GROUP BY b.id
),
clipped AS (
    SELECT *, ST_CollectionExtract(ST_Intersection(boundary, buffers), 3) AS coverage
    FROM per_city
),
-- Share of each block piece's area within the coverage. MATERIALIZED so the
-- intersection is computed once, not once per population column.
covered_pieces AS MATERIALIZED (
    SELECT
        c.id,
        u.population,
        u.population_5_17,
        ST_Area(ST_Intersection(u.geom, c.coverage)) / ST_Area(u.geom) AS share
    FROM clipped c
    JOIN population_units u ON u.city = c.city AND ST_Intersects(u.geom, c.coverage)
),
covered_population AS (
    SELECT
        id,
        sum(population * share) AS covered_population,
        sum(population_5_17 * share) AS covered_population_5_17
    FROM covered_pieces
    GROUP BY id
)
SELECT
    c.city,
    c.eligible_facilities,
    c.excluded_facilities,
    c.contributing_facilities,
    c.contributing_facility_ids,
    c.population,
    coalesce(p.covered_population, 0) AS covered_population,
    c.population_5_17,
    -- NULL only if the data was loaded before migration 003
    CASE WHEN c.population_5_17 IS NOT NULL THEN coalesce(p.covered_population_5_17, 0) END
        AS covered_population_5_17,
    ST_Area(c.boundary) / 1e6 AS city_area_km2,
    coalesce(ST_Area(c.coverage), 0) / 1e6 AS covered_area_km2,
    ST_AsGeoJSON(ST_Transform(c.coverage, 4326), 6)::json AS coverage
FROM clipped c
LEFT JOIN covered_population p ON p.id = c.id
ORDER BY c.city
"""


def percent(part: float, whole: float) -> float:
    return round(100 * part / whole, 1) if whole else 0.0


def optional_round(value: float | None) -> int | None:
    return None if value is None else round(value)


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
            eligible_facilities=row["eligible_facilities"],
            excluded_facilities=row["excluded_facilities"],
            contributing_facilities=row["contributing_facilities"],
            contributing_facility_ids=row["contributing_facility_ids"],
            city_area_km2=round(row["city_area_km2"], 2),
            covered_area_km2=round(row["covered_area_km2"], 2),
            covered_pct=percent(row["covered_area_km2"], row["city_area_km2"]),
            population=row["population"],
            covered_population=round(row["covered_population"]),
            covered_population_pct=percent(row["covered_population"], row["population"]),
            population_5_17=row["population_5_17"],
            covered_population_5_17=optional_round(row["covered_population_5_17"]),
            covered_population_5_17_pct=(
                None
                if row["covered_population_5_17"] is None
                else percent(row["covered_population_5_17"], row["population_5_17"])
            ),
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
