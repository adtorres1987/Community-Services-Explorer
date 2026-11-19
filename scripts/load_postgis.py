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
LIBRARIES_SOURCE = "imls_pls_fy2024_outlets"
BOUNDARIES_SOURCE = "census_tiger_2026_place"
# Name kept from the first load so re-runs replace those rows; the units now also
# carry the DHC population aged 5-17
POPULATION_SOURCE = "census_2020_pl_blocks"

SCHOOL_ATTRIBUTES = [
    "SchoolLevel", "GradeLow", "GradeHigh", "Charter", "Virtual",
    "DistrictName", "Street", "Zip", "CountyNameGeo", "Website", "EnrollTotal",
]


LIBRARY_ATTRIBUTES = {
    # attributes key: GeoPackage column
    "LibrarySystem": "system",
    "Address": "address",
    "Zip": "zip",
    "Phone": "phone",
    "SquareFeet": "square_feet",
    "AnnualHours": "annual_hours",
    "WeeksOpen": "weeks_open",
}


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
libraries = gpd.read_file(GPKG_PATH, layer="libraries")
cities = gpd.read_file(GPKG_PATH, layer="city_boundaries")
units = gpd.read_file(GPKG_PATH, layer="population_units")
layers = {"schools": schools, "libraries": libraries, "city_boundaries": cities, "population_units": units}
for name, layer in layers.items():
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
    cur.execute("DELETE FROM facilities WHERE source_name IN (%s, %s)", (SCHOOLS_SOURCE, LIBRARIES_SOURCE))
    cur.execute("DELETE FROM city_boundaries WHERE source_name = %s", (BOUNDARIES_SOURCE,))

    cur.executemany(
        """
        INSERT INTO city_boundaries (
            geoid, name, place_type, population, population_5_17, source_name, geom
        )
        VALUES (%s, %s, %s, %s, %s, %s, ST_Multi(ST_GeomFromWKB(%s, %s)))
        """,
        [
            (r["geoid"], r["city"], place_type(r["name_lsad"]), r["population"],
             r["population_5_17"], BOUNDARIES_SOURCE, r["wkb"], SRID)
            for r in records(cities)
        ],
    )

    cur.executemany(
        """
        INSERT INTO population_units (geoid20, city, source_name, population, population_5_17, geom)
        VALUES (%s, %s, %s, %s, %s, ST_Multi(ST_GeomFromWKB(%s, %s)))
        """,
        [
            (r["geoid20"], r["city"], POPULATION_SOURCE, r["population"], r["population_5_17"],
             r["wkb"], SRID)
            for r in records(units)
        ],
    )

    insert_facility = """
        INSERT INTO facilities (
            source_id, source_name, name, facility_type, facility_subtype, city,
            address_city, in_study_area, proximity_eligible, attributes, geom
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, ST_GeomFromWKB(%s, %s))
    """
    cur.executemany(
        insert_facility,
        [
            (
                r["CDSCode"], SCHOOLS_SOURCE, r["SchoolName"], "school", r["SchoolType"],
                r["study_city"], r["City"], r["in_study_area"], r["proximity_eligible"],
                Jsonb({key: r[key] for key in SCHOOL_ATTRIBUTES}),
                r["wkb"], SRID,
            )
            for r in records(schools)
        ],
    )
    cur.executemany(
        insert_facility,
        [
            (
                r["library_id"], LIBRARIES_SOURCE, r["name"], "library", r["outlet_type"],
                r["study_city"], r["address_city"], r["in_study_area"], r["proximity_eligible"],
                Jsonb({key: r[column] for key, column in LIBRARY_ATTRIBUTES.items()}),
                r["wkb"], SRID,
            )
            for r in records(libraries)
        ],
    )

    counts = {}
    for name, table, source in (
        ("city_boundaries", "city_boundaries", BOUNDARIES_SOURCE),
        ("population_units", "population_units", POPULATION_SOURCE),
        ("schools", "facilities", SCHOOLS_SOURCE),
        ("libraries", "facilities", LIBRARIES_SOURCE),
    ):
        cur.execute(f"SELECT count(*) FROM {table} WHERE source_name = %s", (source,))
        counts[name] = cur.fetchone()[0]

    expected = {name: len(layer) for name, layer in layers.items()}
    # Raising inside the block rolls the transaction back
    if counts != expected:
        raise RuntimeError(f"Row count mismatch: loaded {counts}, expected {expected}")

print(" | ".join(f"{table}: {count} rows" for table, count in counts.items()))
