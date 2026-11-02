from psycopg import Connection

from app.schemas.facilities import FacilityCollection, FacilityFeature, FacilityProperties

FACILITY_SELECT = """
SELECT
    id, name, facility_type, facility_subtype, city,
    in_city_limits, proximity_eligible, attributes,
    ST_AsGeoJSON(ST_Transform(geom, 4326), 6)::json AS geometry
FROM facilities
"""


def to_feature(row: dict) -> FacilityFeature:
    geometry = row.pop("geometry")
    return FacilityFeature(id=row["id"], geometry=geometry, properties=FacilityProperties(**row))


def list_facilities(
    conn: Connection,
    city: str | None,
    facility_type: str | None,
    facility_subtype: str | None,
) -> FacilityCollection:
    rows = conn.execute(
        FACILITY_SELECT
        + """
        WHERE (%(city)s::text IS NULL OR city = %(city)s)
          AND (%(facility_type)s::text IS NULL OR facility_type = %(facility_type)s)
          AND (%(facility_subtype)s::text IS NULL OR facility_subtype = %(facility_subtype)s)
        ORDER BY city, name
        """,
        {"city": city, "facility_type": facility_type, "facility_subtype": facility_subtype},
    ).fetchall()
    return FacilityCollection(features=[to_feature(row) for row in rows])


def get_facility(conn: Connection, facility_id: int) -> FacilityFeature | None:
    row = conn.execute(FACILITY_SELECT + "WHERE id = %s", (facility_id,)).fetchone()
    return to_feature(row) if row else None
