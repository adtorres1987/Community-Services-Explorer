"""Load data/processed/study_area.gpkg into PostGIS.

Replaces the rows of each source in one transaction, so it can be re-run.
Connection settings come from .env (see .env.example).
"""
from pathlib import Path
import os

import geopandas as gpd
import psycopg
from dotenv import load_dotenv
from psycopg.types.json import Jsonb

ROOT = Path(__file__).resolve().parents[1]
GPKG_PATH = ROOT / "data/processed/study_area.gpkg"

SRID = 26911
SCHOOLS_SOURCE = "cde_public_schools_2025_26"
BOUNDARIES_SOURCE = "census_tiger_2026_place"

SCHOOL_ATTRIBUTES = [
    "SchoolLevel", "GradeLow", "GradeHigh", "Charter", "Virtual",
    "DistrictName", "Street", "Zip", "Website", "EnrollTotal",
]


def records(gdf):
    """Rows as dicts with native Python values and None instead of NaN."""
    df = gdf.drop(columns="geometry").astype(object)
    rows = df.where(df.notna(), None).to_dict("records")
    for row, geom in zip(rows, gdf.geometry):
        row["wkb"] = geom.wkb
    return rows


if not GPKG_PATH.exists():
    raise FileNotFoundError(f"{GPKG_PATH} — run scripts/prepare_schools.py first")

load_dotenv(ROOT / ".env")

schools = gpd.read_file(GPKG_PATH, layer="schools")
cities = gpd.read_file(GPKG_PATH, layer="city_boundaries")
for name, layer in (("schools", schools), ("city_boundaries", cities)):
    if layer.crs.to_epsg() != SRID:
        raise ValueError(f"{name} CRS is {layer.crs}, expected EPSG:{SRID}")

conninfo = psycopg.conninfo.make_conninfo(
    host=os.environ["POSTGRES_HOST"],
    port=os.environ["POSTGRES_PORT"],
    dbname=os.environ["POSTGRES_DB"],
    user=os.environ["POSTGRES_USER"],
    password=os.environ["POSTGRES_PASSWORD"],
)

with psycopg.connect(conninfo) as conn, conn.cursor() as cur:
    cur.execute("DELETE FROM city_boundaries WHERE source_name = %s", (BOUNDARIES_SOURCE,))
    cur.executemany(
        """
        INSERT INTO city_boundaries (geoid, name, source_name, geom)
        VALUES (%s, %s, %s, ST_Multi(ST_GeomFromWKB(%s, %s)))
        """,
        [(r["geoid"], r["city"], BOUNDARIES_SOURCE, r["wkb"], SRID) for r in records(cities)],
    )

    cur.execute("DELETE FROM facilities WHERE source_name = %s", (SCHOOLS_SOURCE,))
    cur.executemany(
        """
        INSERT INTO facilities (
            source_id, source_name, name, facility_type, facility_subtype, city,
            in_city_limits, proximity_eligible, attributes, geom
        )
        VALUES (%s, %s, %s, 'school', %s, %s, %s, %s, %s, ST_GeomFromWKB(%s, %s))
        """,
        [
            (
                r["CDSCode"], SCHOOLS_SOURCE, r["SchoolName"], r["SchoolType"], r["City"],
                r["in_city_limits"], r["proximity_eligible"],
                Jsonb({key: r[key] for key in SCHOOL_ATTRIBUTES}),
                r["wkb"], SRID,
            )
            for r in records(schools)
        ],
    )

    cur.execute("SELECT count(*) FROM city_boundaries WHERE source_name = %s", (BOUNDARIES_SOURCE,))
    loaded_cities = cur.fetchone()[0]
    cur.execute("SELECT count(*) FROM facilities WHERE source_name = %s", (SCHOOLS_SOURCE,))
    loaded_schools = cur.fetchone()[0]

    # Raising inside the block rolls the transaction back
    if (loaded_cities, loaded_schools) != (len(cities), len(schools)):
        raise RuntimeError(
            f"Row count mismatch: cities {loaded_cities}/{len(cities)}, "
            f"schools {loaded_schools}/{len(schools)}"
        )

print(f"city_boundaries: {loaded_cities} rows | facilities: {loaded_schools} rows")
