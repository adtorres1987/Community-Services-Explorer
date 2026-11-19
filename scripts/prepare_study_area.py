"""Build the study-area dataset: nine contiguous places in the San Bernardino Valley.

Writes data/processed/study_area.gpkg (EPSG:26911) with four layers:

- schools: active public schools inside a study place, plus "context" schools
  within SCHOOL_CONTEXT_DISTANCE_M of a study place that only contribute to coverage
- libraries: public library outlets (central and branch), with context libraries
  within LIBRARY_CONTEXT_DISTANCE_M
- city_boundaries: the study place boundaries with their 2020 population, total
  and aged 5-17
- population_units: 2020 census blocks clipped to each place, with both
  populations apportioned by area

"City" in column names means study place; Mentone is an unincorporated
census-designated place (CDP), the others are incorporated cities.

Criteria are documented in docs/data-sources.md. Inputs in data/raw/ are
never modified.
"""
from pathlib import Path
import csv
import string

import geopandas as gpd
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data/raw"
SCHOOLS_PATH = RAW / "california-public-schools-2025-2026.geojson"
PLACES_PATH = RAW / "tl_2026_06_place/tl_2026_06_place.shp"
BLOCKS_PATH = RAW / "tl_2020_06071_tabblock20/tl_2020_06071_tabblock20.shp"
PL_GEO_PATH = RAW / "ca2020.pl/cageo2020.pl"
DHC_GEO_PATH = RAW / "ca2020.dhc/cageo2020.dhc"
DHC_P12_PATH = RAW / "ca2020.dhc/ca000062020.dhc"  # segment 6: tables P10, P11, P12, P12A
PLS_DIR = RAW / "pls_fy2024/CSV"  # IMLS Public Libraries Survey FY 2024
LIBRARY_OUTLETS_PATH = PLS_DIR / "pls_fy24_outlet_pud24i.csv"
LIBRARY_SYSTEMS_PATH = PLS_DIR / "PLS_FY24_AE_pud24i.csv"
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
# Largest radius offered for each service: facilities this close to a place can
# cover part of it, so they are kept as context
SCHOOL_CONTEXT_DISTANCE_M = 2000
LIBRARY_CONTEXT_DISTANCE_M = 3200  # 2 miles
# Block geometry tolerance: halves the committed file size, changes total area by ~0.003 %
POPULATION_SIMPLIFY_M = 1.0

# PLS outlet types kept: fixed service points. Bookmobiles (BS) and books-by-mail
# (BM) have no fixed location.
LIBRARY_OUTLET_TYPES = {"CE": "Central", "BR": "Branch"}
LIBRARY_TEMPORARILY_CLOSED = "23"  # STATSTRU
LIBRARY_COLUMNS = [
    "library_id", "name", "outlet_type", "system", "address", "address_city", "zip",
    "phone", "square_feet", "annual_hours", "weeks_open", "LIBNAME", "LATITUDE", "LONGITUD",
]

KEEP_COLUMNS = [
    "CDSCode", "SchoolName", "SchoolType", "SchoolLevel", "GradeLow",
    "GradeHigh", "Status", "Charter", "Virtual", "DistrictName", "Street",
    "City", "Zip", "CountyNameGeo", "Website", "EnrollTotal", "Latitude", "Longitude",
]

# Positions in the P.L. 94-171 geographic header (pipe-delimited, 97 fields)
PL_SUMLEV, PL_GEOCODE, PL_POP100 = 2, 9, 90
PL_BLOCK_SUMLEV = "750"

# DHC geographic header: same 97-field layout; records join to segments by LOGRECNO.
# Blocks are summary level 100 in the DHC (750 is the P.L. 94-171 tabulation block).
DHC_SUMLEV, DHC_LOGRECNO, DHC_GEOCODE = 2, 7, 9
DHC_BLOCK_SUMLEV = "100"
# Segment 6 records: FILEID|STUSAB|CHARITER|CIFSN|LOGRECNO, then P10 (71 cells),
# P11 (73) and P12 (49), per the Census table_segments_dhc.csv
SEGMENT_LOGRECNO = 4
P12_START = 5 + 71 + 73
P12_CELLS = 49
# P12 cells (1-based) for ages 5-9, 10-14 and 15-17: male 4-6, female 28-30
P12_AGE_5_17 = (4, 5, 6, 28, 29, 30)


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
    selected = assign_to_places(active, cities, SCHOOL_CONTEXT_DISTANCE_M)
    # Exclusively virtual schools are administrative addresses, not service locations
    selected["proximity_eligible"] = selected["Virtual"] != "V"
    return selected


def assign_to_places(
    facilities: gpd.GeoDataFrame, cities: gpd.GeoDataFrame, context_distance_m: float
) -> gpd.GeoDataFrame:
    """Facilities inside a study place, plus context facilities near one.

    Adds study_city (the place whose boundary contains the facility, or None)
    and in_study_area. Context facilities are within context_distance_m of a
    place, in any county, and only contribute to proximity coverage.
    """
    joined = gpd.sjoin(facilities, cities[["city", "geometry"]], how="left", predicate="within")
    if joined.index.duplicated().any():
        raise ValueError("A facility falls within more than one study place")
    facilities = facilities.assign(
        study_city=joined["city"].astype(object).where(joined["city"].notna(), None)
    )
    in_study_area = facilities["study_city"].notna()
    near = facilities.geometry.distance(cities.union_all()) <= context_distance_m
    selected = facilities[in_study_area | near].copy()
    selected["in_study_area"] = selected["study_city"].notna()
    return selected.reset_index(drop=True)


LOWERCASE_WORDS = {"and", "of", "for", "the", "at"}


def display_case(value):
    """PLS text is upper case: "656 N. 9TH ST." -> "656 N. 9th St."."""
    if not isinstance(value, str):
        return value
    words = string.capwords(value).split(" ")
    return " ".join(
        word.lower() if i > 0 and word.lower() in LOWERCASE_WORDS else word
        for i, word in enumerate(words)
    )


def pls_number(series: pd.Series) -> pd.Series:
    """PLS numeric fields use negative codes (-1, -3, -9) for missing values."""
    values = pd.to_numeric(series, errors="coerce")
    return values.where(values >= 0).astype("Int64")


def select_libraries(
    outlets: pd.DataFrame, systems: pd.DataFrame, cities: gpd.GeoDataFrame
) -> gpd.GeoDataFrame:
    """Public library outlets inside a study place, plus context libraries near one.

    Keeps California outlets of systems that meet the FSCS public library
    definition (C_FSCS = Y; excludes the county law libraries), central and branch
    outlets only, and not temporarily closed. All are proximity eligible.
    """
    if outlets[["FSCSKEY", "FSCS_SEQ"]].duplicated().any():
        raise ValueError("Duplicate FSCSKEY/FSCS_SEQ values in the PLS outlet file")
    keep = (
        (outlets["STABR"] == "CA")
        & (outlets["C_FSCS"] == "Y")
        & outlets["C_OUT_TY"].isin(LIBRARY_OUTLET_TYPES)
        & (outlets["STATSTRU"] != LIBRARY_TEMPORARILY_CLOSED)
    )
    libraries = outlets[keep].copy()
    coordinates = libraries[["LONGITUD", "LATITUDE"]].apply(pd.to_numeric, errors="coerce")
    if coordinates.isna().any().any():
        raise ValueError("PLS outlets without coordinates; review before continuing")

    names = systems.drop_duplicates("FSCSKEY").set_index("FSCSKEY")["LIBNAME"]
    libraries = libraries.assign(
        library_id=libraries["FSCSKEY"] + "-" + libraries["FSCS_SEQ"],
        name=libraries["LIBNAME"].map(display_case),
        outlet_type=libraries["C_OUT_TY"].map(LIBRARY_OUTLET_TYPES),
        system=libraries["FSCSKEY"].map(names).map(display_case),
        address=libraries["ADDRESS"].map(display_case),
        address_city=libraries["CITY"].map(display_case),
        zip=libraries["ZIP"],
        phone=libraries["PHONE"],
        square_feet=pls_number(libraries["SQ_FEET"]),
        annual_hours=pls_number(libraries["HOURS"]),
        weeks_open=pls_number(libraries["WKS_OPEN"]),
        LATITUDE=coordinates["LATITUDE"],
        LONGITUD=coordinates["LONGITUD"],
    )
    if libraries["system"].isna().any():
        raise ValueError("PLS outlets without a matching library system")
    # PLS coordinates are geocoded latitude/longitude (WGS84)
    libraries = gpd.GeoDataFrame(
        libraries[LIBRARY_COLUMNS],
        geometry=gpd.points_from_xy(coordinates["LONGITUD"], coordinates["LATITUDE"]),
        crs="EPSG:4326",
    ).to_crs(WORKING_CRS)
    selected = assign_to_places(libraries, cities, LIBRARY_CONTEXT_DISTANCE_M)
    selected["proximity_eligible"] = True
    return selected


def read_block_population(path: Path, county_geocode: str = COUNTY_GEOCODE) -> pd.DataFrame:
    """2020 total population (POP100) of each census block in the county."""
    rows = []
    with path.open(encoding="latin-1", newline="") as f:
        for record in csv.reader(f, delimiter="|"):
            if record[PL_SUMLEV] == PL_BLOCK_SUMLEV and record[PL_GEOCODE].startswith(county_geocode):
                rows.append((record[PL_GEOCODE], int(record[PL_POP100])))
    return pd.DataFrame(rows, columns=["GEOID20", "population"])


def read_block_age_5_17(
    geo_path: Path, segment_path: Path, county_geocode: str = COUNTY_GEOCODE
) -> pd.DataFrame:
    """2020 population aged 5-17 of each census block in the county (DHC table P12)."""
    geocodes = {}
    with geo_path.open(encoding="latin-1", newline="") as f:
        for record in csv.reader(f, delimiter="|"):
            if record[DHC_SUMLEV] == DHC_BLOCK_SUMLEV and record[DHC_GEOCODE].startswith(county_geocode):
                geocodes[record[DHC_LOGRECNO]] = record[DHC_GEOCODE]

    rows = []
    with segment_path.open(encoding="latin-1", newline="") as f:
        for record in csv.reader(f, delimiter="|"):
            geocode = geocodes.get(record[SEGMENT_LOGRECNO])
            if geocode is None:
                continue
            p12 = [int(value) for value in record[P12_START:P12_START + P12_CELLS]]
            # Total = male + female, and each is the sum of its age groups
            if p12[0] != p12[1] + p12[25] or p12[1] != sum(p12[2:25]) or p12[25] != sum(p12[26:49]):
                raise ValueError(f"Inconsistent P12 record for block {geocode}")
            rows.append((geocode, sum(p12[cell - 1] for cell in P12_AGE_5_17)))

    if len(rows) != len(geocodes):
        raise ValueError(f"P12 records found for {len(rows)} of {len(geocodes)} blocks")
    return pd.DataFrame(rows, columns=["GEOID20", "population_5_17"])


def apportion_population(
    blocks: gpd.GeoDataFrame, population: pd.DataFrame, cities: gpd.GeoDataFrame
) -> gpd.GeoDataFrame:
    """Clip blocks to the study cities and apportion each block's population by area.

    Every column of `population` other than GEOID20 is a count (total, aged 5-17).
    2020 blocks do not nest exactly in 2026 city boundaries, so a block split by a
    boundary contributes to each side in proportion to its area (assumes uniform
    density within the block).
    """
    counts = [column for column in population.columns if column != "GEOID20"]
    blocks = blocks[["GEOID20", "geometry"]].merge(population, on="GEOID20", how="left", validate="1:1")
    if blocks[counts].isna().any().any():
        raise ValueError("Census blocks without population records")
    blocks = blocks.to_crs(WORKING_CRS)
    blocks["block_area"] = blocks.area

    pieces = gpd.overlay(blocks, cities[["city", "geometry"]], how="intersection", keep_geom_type=True)
    pieces = pieces[pieces.area > 0]
    for column in counts:
        pieces[column] = pieces[column] * pieces.area / pieces["block_area"]
    # Simplify after apportioning, so the population values are exact
    pieces["geometry"] = pieces.simplify(POPULATION_SIMPLIFY_M, preserve_topology=True)
    pieces = pieces.rename(columns={"GEOID20": "geoid20"})
    return pieces[["geoid20", "city", *counts, "geometry"]].reset_index(drop=True)


def main() -> None:
    for path in (
        SCHOOLS_PATH, PLACES_PATH, BLOCKS_PATH, PL_GEO_PATH, DHC_GEO_PATH, DHC_P12_PATH,
        LIBRARY_OUTLETS_PATH, LIBRARY_SYSTEMS_PATH,
    ):
        if not path.exists():
            raise FileNotFoundError(f"{path} — run scripts/download_data.py first")

    cities = select_city_boundaries(gpd.read_file(PLACES_PATH))

    schools = gpd.read_file(SCHOOLS_PATH)
    print("Schools read:", len(schools))
    selected = select_schools(schools, cities)
    study = selected[selected["in_study_area"]]
    print("Schools in study cities:", len(study), "| context schools:", (~selected["in_study_area"]).sum())
    print("Not proximity eligible (Virtual = V):", (~selected["proximity_eligible"]).sum())

    libraries = select_libraries(
        pd.read_csv(LIBRARY_OUTLETS_PATH, dtype=str, encoding="latin-1"),
        pd.read_csv(LIBRARY_SYSTEMS_PATH, dtype=str, encoding="latin-1"),
        cities,
    )
    print(
        "Libraries in study places:", libraries["in_study_area"].sum(),
        "| context libraries:", (~libraries["in_study_area"]).sum(),
    )

    population = read_block_population(PL_GEO_PATH).merge(
        read_block_age_5_17(DHC_GEO_PATH, DHC_P12_PATH), on="GEOID20", how="outer", validate="1:1"
    )
    if population.isna().any().any():
        raise ValueError("P.L. 94-171 and DHC blocks do not match")
    if (population["population_5_17"] > population["population"]).any():
        raise ValueError("Population aged 5-17 exceeds total population")
    print(
        "County blocks:", len(population),
        "| county population:", population["population"].sum(),
        "| aged 5-17:", population["population_5_17"].sum(),
    )
    units = apportion_population(gpd.read_file(BLOCKS_PATH), population, cities)
    for column in ("population", "population_5_17"):
        totals = units.groupby("city")[column].sum()
        cities[column] = cities["city"].map(totals).fillna(0).round().astype(int)
    print("Population in study cities:", cities["population"].sum(), "| aged 5-17:", cities["population_5_17"].sum())

    summary = (
        cities.set_index("city")[["population", "population_5_17"]]
        .join(study.groupby("study_city").size().rename("schools"))
        .join(libraries[libraries["in_study_area"]].groupby("study_city").size().rename("libraries"))
        .fillna({"libraries": 0})
    )
    print(summary.sort_values("population", ascending=False).to_string())

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.unlink(missing_ok=True)
    selected.to_file(OUTPUT_PATH, layer="schools", driver="GPKG")
    libraries.to_file(OUTPUT_PATH, layer="libraries", driver="GPKG")
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
