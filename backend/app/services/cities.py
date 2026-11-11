from psycopg import Connection

from app.schemas.cities import CityCollection, CityFeature, CityProperties


def list_cities(conn: Connection) -> CityCollection:
    rows = conn.execute(
        """
        SELECT
            b.geoid,
            b.name,
            b.place_type,
            b.population,
            b.population_5_17,
            ST_Area(b.geom) / 1e6 AS area_km2,
            (SELECT count(*) FROM facilities f WHERE f.city = b.name) AS facility_count,
            ST_AsGeoJSON(ST_Transform(b.geom, 4326), 6)::json AS geometry
        FROM city_boundaries b
        ORDER BY b.name
        """
    ).fetchall()
    return CityCollection(
        features=[
            CityFeature(
                id=row["geoid"],
                geometry=row["geometry"],
                properties=CityProperties(
                    name=row["name"],
                    geoid=row["geoid"],
                    place_type=row["place_type"],
                    area_km2=round(row["area_km2"], 2),
                    population=row["population"],
                    population_5_17=row["population_5_17"],
                    facility_count=row["facility_count"],
                ),
            )
            for row in rows
        ]
    )


def city_exists(conn: Connection, name: str) -> bool:
    row = conn.execute("SELECT 1 FROM city_boundaries WHERE name = %s", (name,)).fetchone()
    return row is not None
