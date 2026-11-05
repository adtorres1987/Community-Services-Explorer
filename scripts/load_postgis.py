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
POPULATION_SOURCE = "census_2020_pl_blocks"

SCHOOL_ATTRIBUTES = [
    "SchoolLevel", "GradeLow", "GradeHigh", "Charter", "Virtual",
    "DistrictName", "Street", "Zip", "CountyNameGeo", "Website", "EnrollTotal",
]


def records(gdf):
    """Rows as dicts with native Python values and None instead of NaN."""
    df = gdf.drop(columns="geometry").astype(object)
    rows = df.where(df.notna(), None).to_dict("records")
    for row, geom in zip(rows, gdf.geometry):
        row["wkb"] = geom.wkb
    return rows


def place_type(name_lsad: str) -> str:
    # NAMELSAD ends with the legal/statistical area description, e.g. "Mentone CDP"
    return name_lsad.rsplit(" ", 1)[-1]


if not GPKG_PATH.exists():
    raise FileNotFoundError(f"{GPKG_PATH} — run scripts/prepare_study_area.py first")

load_dotenv(ROOT / ".env")

schools = gpd.read_file(GPKG_PATH, layer="schools")
cities = gpd.read_file(GPKG_PATH, layer="city_boundaries")
units = gpd.read_file(GPKG_PATH, layer="population_units")
for name, layer in (("schools", schools), ("city_boundaries", cities), ("population_units", units)):
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
    # Population units reference city boundaries, so they are removed first
    cur.execute("DELETE FROM population_units WHERE source_name = %s", (POPULATION_SOURCE,))
    cur.execute("DELETE FROM facilities WHERE source_name = %s", (SCHOOLS_SOURCE,))
    cur.execute("DELETE FROM city_boundaries WHERE source_name = %s", (BOUNDARIES_SOURCE,))

    cur.executemany(
        """
        INSERT INTO city_boundaries (geoid, name, place_type, population, source_name, geom)
        VALUES (%s, %s, %s, %s, %s, ST_Multi(ST_GeomFromWKB(%s, %s)))
        """,
        [
            (r["geoid"], r["city"], place_type(r["name_lsad"]), r["population"],
             BOUNDARIES_SOURCE, r["wkb"], SRID)
            for r in records(cities)
        ],
    )

    cur.executemany(
        """
        INSERT INTO population_units (geoid20, city, source_name, population, geom)
        VALUES (%s, %s, %s, %s, ST_Multi(ST_GeomFromWKB(%s, %s)))
        """,
        [
            (r["geoid20"], r["city"], POPULATION_SOURCE, r["population"], r["wkb"], SRID)
            for r in records(units)
        ],
    )

    cur.executemany(
        """
        INSERT INTO facilities (
            source_id, source_name, name, facility_type, facility_subtype, city,
            address_city, in_study_area, proximity_eligible, attributes, geom
        )
        VALUES (%s, %s, %s, 'school', %s, %s, %s, %s, %s, %s, ST_GeomFromWKB(%s, %s))
        """,
        [
            (
                r["CDSCode"], SCHOOLS_SOURCE, r["SchoolName"], r["SchoolType"], r["study_city"],
                r["City"], r["in_study_area"], r["proximity_eligible"],
                Jsonb({key: r[key] for key in SCHOOL_ATTRIBUTES}),
                r["wkb"], SRID,
            )
            for r in records(schools)
        ],
    )

    counts = {}
    for table, source in (
        ("city_boundaries", BOUNDARIES_SOURCE),
        ("population_units", POPULATION_SOURCE),
        ("facilities", SCHOOLS_SOURCE),
    ):
        cur.execute(f"SELECT count(*) FROM {table} WHERE source_name = %s", (source,))
        counts[table] = cur.fetchone()[0]

    expected = {"city_boundaries": len(cities), "population_units": len(units), "facilities": len(schools)}
    # Raising inside the block rolls the transaction back
    if counts != expected:
        raise RuntimeError(f"Row count mismatch: loaded {counts}, expected {expected}")

print(" | ".join(f"{table}: {count} rows" for table, count in counts.items()))
