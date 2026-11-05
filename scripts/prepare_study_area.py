"""Build the study-area dataset: nine contiguous places in the San Bernardino Valley.

Writes data/processed/study_area.gpkg (EPSG:26911) with three layers:

- schools: active public schools inside a study place, plus "context" schools
  within CONTEXT_DISTANCE_M of a study place that only contribute to coverage
- city_boundaries: the study place boundaries with their 2020 population
- population_units: 2020 census blocks clipped to each place, with population
  apportioned by area

"City" in column names means study place; Mentone is an unincorporated
census-designated place (CDP), the others are incorporated cities.

Criteria are documented in docs/data-sources.md. Inputs in data/raw/ are
never modified.
"""
from pathlib import Path
import csv

import geopandas as gpd
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data/raw"
SCHOOLS_PATH = RAW / "california-public-schools-2025-2026.geojson"
PLACES_PATH = RAW / "tl_2026_06_place/tl_2026_06_place.shp"
BLOCKS_PATH = RAW / "tl_2020_06071_tabblock20/tl_2020_06071_tabblock20.shp"
PL_GEO_PATH = RAW / "ca2020.pl/cageo2020.pl"
OUTPUT_PATH = ROOT / "data/processed/study_area.gpkg"

COUNTY_GEOCODE = "06071"  # San Bernardino County, CA
# TIGER/Line place GEOIDs, so the selection does not depend on names
STUDY_PLACES = {
    "0614890": "Colton",
    "0630658": "Grand Terrace",
    "0633588": "Highland",
    "0642370": "Loma Linda",
    "0646884": "Mentone",  # CDP (LSAD 57)
    "0659962": "Redlands",
    "0660466": "Rialto",
    "0665000": "San Bernardino",
    "0687042": "Yucaipa",
}

SOURCE_CRS = "EPSG:3857"
WORKING_CRS = "EPSG:26911"  # NAD83 / UTM zone 11N, metres
# Largest radius offered by the API: schools this close to a city can cover part of it
CONTEXT_DISTANCE_M = 2000
# Block geometry tolerance: halves the committed file size, changes total area by ~0.003 %
POPULATION_SIMPLIFY_M = 1.0

KEEP_COLUMNS = [
    "CDSCode", "SchoolName", "SchoolType", "SchoolLevel", "GradeLow",
    "GradeHigh", "Status", "Charter", "Virtual", "DistrictName", "Street",
    "City", "Zip", "CountyNameGeo", "Website", "EnrollTotal", "Latitude", "Longitude",
]

# Positions in the P.L. 94-171 geographic header (pipe-delimited, 97 fields)
PL_SUMLEV, PL_GEOCODE, PL_POP100 = 2, 9, 90
PL_BLOCK_SUMLEV = "750"


def select_city_boundaries(places: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    """Boundaries of the study places, in the working CRS."""
    cities = places[places["GEOID"].isin(STUDY_PLACES)]
    if dict(zip(cities["GEOID"], cities["NAME"])) != STUDY_PLACES or len(cities) != len(STUDY_PLACES):
        raise ValueError(
            f"Expected places {STUDY_PLACES}, got {dict(zip(cities['GEOID'], cities['NAME']))}"
        )
    cities = (
        cities[["GEOID", "NAME", "NAMELSAD", "LSAD", "geometry"]]
        .rename(columns={"GEOID": "geoid", "NAME": "city", "NAMELSAD": "name_lsad", "LSAD": "lsad"})
        .to_crs(WORKING_CRS)
        .reset_index(drop=True)
    )
    if not cities.is_valid.all():
        raise ValueError("Invalid city boundary geometry")
    return cities


def select_schools(schools: gpd.GeoDataFrame, cities: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    """Active schools inside a study city, plus context schools near one.

    Adds study_city (the city whose boundary contains the school, or None),
    in_study_area and proximity_eligible.
    """
    if schools.crs != SOURCE_CRS:
        raise ValueError(f"Unexpected schools CRS: {schools.crs}")
    if schools["CDSCode"].duplicated().any():
        raise ValueError("Duplicate CDSCode values in source")

    active = schools[schools["Status"] == "Active"]
    print("Excluded (Status != Active):", len(schools) - len(active))

    bad_geometry = active.geometry.isna() | active.geometry.is_empty | ~active.is_valid
    if bad_geometry.any():
        print(active.loc[bad_geometry, ["CDSCode", "SchoolName"]].to_string(index=False))
        raise ValueError("Invalid school geometries; review before continuing")

    active = active[KEEP_COLUMNS + ["geometry"]].to_crs(WORKING_CRS)
    joined = gpd.sjoin(active, cities[["city", "geometry"]], how="left", predicate="within")
    if joined.index.duplicated().any():
        raise ValueError("A school falls within more than one study city")
    active = active.assign(study_city=joined["city"].astype(object).where(joined["city"].notna(), None))

    in_study_area = active["study_city"].notna()
    near = active.geometry.distance(cities.union_all()) <= CONTEXT_DISTANCE_M
    selected = active[in_study_area | near].copy()
    selected["in_study_area"] = selected["study_city"].notna()
    # Exclusively virtual schools are administrative addresses, not service locations
    selected["proximity_eligible"] = selected["Virtual"] != "V"
    return selected.reset_index(drop=True)


def read_block_population(path: Path, county_geocode: str = COUNTY_GEOCODE) -> pd.DataFrame:
    """2020 total population (POP100) of each census block in the county."""
    rows = []
    with path.open(encoding="latin-1", newline="") as f:
        for record in csv.reader(f, delimiter="|"):
            if record[PL_SUMLEV] == PL_BLOCK_SUMLEV and record[PL_GEOCODE].startswith(county_geocode):
                rows.append((record[PL_GEOCODE], int(record[PL_POP100])))
    return pd.DataFrame(rows, columns=["GEOID20", "population"])


def apportion_population(
    blocks: gpd.GeoDataFrame, population: pd.DataFrame, cities: gpd.GeoDataFrame
) -> gpd.GeoDataFrame:
    """Clip blocks to the study cities and apportion each block's population by area.

    2020 blocks do not nest exactly in 2026 city boundaries, so a block split by a
    boundary contributes to each side in proportion to its area (assumes uniform
    density within the block).
    """
    blocks = blocks[["GEOID20", "geometry"]].merge(population, on="GEOID20", how="left", validate="1:1")
    if blocks["population"].isna().any():
        raise ValueError("Census blocks without population records")
    blocks = blocks.to_crs(WORKING_CRS)
    blocks["block_area"] = blocks.area

    pieces = gpd.overlay(blocks, cities[["city", "geometry"]], how="intersection", keep_geom_type=True)
    pieces = pieces[pieces.area > 0]
    pieces["population"] = pieces["population"] * pieces.area / pieces["block_area"]
    # Simplify after apportioning, so the population values are exact
    pieces["geometry"] = pieces.simplify(POPULATION_SIMPLIFY_M, preserve_topology=True)
    pieces = pieces.rename(columns={"GEOID20": "geoid20"})
    return pieces[["geoid20", "city", "population", "geometry"]].reset_index(drop=True)


def main() -> None:
    for path in (SCHOOLS_PATH, PLACES_PATH, BLOCKS_PATH, PL_GEO_PATH):
        if not path.exists():
            raise FileNotFoundError(f"{path} — run scripts/download_data.py first")

    cities = select_city_boundaries(gpd.read_file(PLACES_PATH))

    schools = gpd.read_file(SCHOOLS_PATH)
    print("Schools read:", len(schools))
    selected = select_schools(schools, cities)
    study = selected[selected["in_study_area"]]
    print("Schools in study cities:", len(study), "| context schools:", (~selected["in_study_area"]).sum())
    print("Not proximity eligible (Virtual = V):", (~selected["proximity_eligible"]).sum())

    population = read_block_population(PL_GEO_PATH)
    print("County blocks:", len(population), "| county population:", population["population"].sum())
    units = apportion_population(gpd.read_file(BLOCKS_PATH), population, cities)
    cities["population"] = (
        cities["city"].map(units.groupby("city")["population"].sum()).fillna(0).round().astype(int)
    )
    print("Population in study cities:", cities["population"].sum())

    summary = cities.set_index("city")[["population"]].join(study.groupby("study_city").size().rename("schools"))
    print(summary.sort_values("population", ascending=False).to_string())

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.unlink(missing_ok=True)
    selected.to_file(OUTPUT_PATH, layer="schools", driver="GPKG")
    cities.to_file(OUTPUT_PATH, layer="city_boundaries", driver="GPKG")
    # No GeoPackage spatial index: PostGIS builds its own, and it keeps the committed file small
    units.to_file(
        OUTPUT_PATH,
        layer="population_units",
        driver="GPKG",
        promote_to_multi=True,
        layer_options={"SPATIAL_INDEX": "NO"},
    )
    print("Output:", OUTPUT_PATH.relative_to(ROOT), "| CRS:", WORKING_CRS)


if __name__ == "__main__":
    main()
