"""Filter, validate and reproject schools for the Redlands/Yucaipa study area.

Criteria are documented in docs/data-sources.md. Inputs in data/raw/ are
never modified; output goes to data/processed/study_area.gpkg.
"""
from pathlib import Path
import geopandas as gpd

ROOT = Path(__file__).resolve().parents[1]
SCHOOLS_PATH = ROOT / "data/raw/california-public-schools-2025-2026.geojson"
PLACES_PATH = ROOT / "data/raw/tl_2026_06_place/tl_2026_06_place.shp"
OUTPUT_PATH = ROOT / "data/processed/study_area.gpkg"

STUDY_CITIES = ["Redlands", "Yucaipa"]
SOURCE_CRS = "EPSG:3857"
WORKING_CRS = "EPSG:26911"  # NAD83 / UTM zone 11N, metres
MAX_DISTANCE_TO_CITY_M = 5000

KEEP_COLUMNS = [
    "CDSCode", "SchoolName", "SchoolType", "SchoolLevel", "GradeLow",
    "GradeHigh", "Status", "Charter", "Virtual", "DistrictName", "Street",
    "City", "Zip", "Website", "EnrollTotal", "Latitude", "Longitude",
]


def select_city_boundaries(places: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    """Incorporated city boundaries (LSAD 25) for the study cities, in the working CRS."""
    cities = places[places["NAME"].isin(STUDY_CITIES) & (places["LSAD"] == "25")]
    if sorted(cities["NAME"]) != sorted(STUDY_CITIES):
        raise ValueError(f"Expected one boundary per city, got {cities['NAME'].tolist()}")
    cities = (
        cities[["GEOID", "NAME", "NAMELSAD", "geometry"]]
        .rename(columns={"GEOID": "geoid", "NAME": "city", "NAMELSAD": "name_lsad"})
        .to_crs(WORKING_CRS)
    )
    if not cities.is_valid.all():
        raise ValueError("Invalid city boundary geometry")
    return cities


def filter_schools(schools: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    """Active schools whose address city is a study city, reprojected to the working CRS."""
    if schools.crs != SOURCE_CRS:
        raise ValueError(f"Unexpected schools CRS: {schools.crs}")
    if schools["CDSCode"].duplicated().any():
        raise ValueError("Duplicate CDSCode values in source")

    in_cities = schools["City"].isin(STUDY_CITIES)
    print("Excluded (City not in study area):", (~in_cities).sum())
    study = schools[in_cities]

    active = study["Status"] == "Active"
    print("Excluded (Status != Active):", (~active).sum())
    study = study[active]

    bad_geometry = study.geometry.isna() | study.geometry.is_empty | ~study.is_valid
    if bad_geometry.any():
        print("Invalid geometries:")
        print(study.loc[bad_geometry, ["CDSCode", "SchoolName"]].to_string(index=False))
        raise ValueError("Invalid school geometries; review before continuing")

    return study[KEEP_COLUMNS + ["geometry"]].to_crs(WORKING_CRS)


def add_flags(study: gpd.GeoDataFrame, cities: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    """Add in_city_limits and proximity_eligible; fail on schools far from their city."""
    study = study.copy()
    boundary_by_city = cities.set_index("city").geometry

    # A point counts as inside its address city only if it falls within that city's boundary
    study["in_city_limits"] = [
        boundary_by_city[city].contains(point)
        for city, point in zip(study["City"], study.geometry)
    ]
    # Exclusively virtual schools are administrative addresses, not service locations
    study["proximity_eligible"] = study["Virtual"] != "V"

    # Sanity check: every school should be near its city (catches CRS or geocoding errors)
    distance_m = [
        boundary_by_city[city].distance(point)
        for city, point in zip(study["City"], study.geometry)
    ]
    if max(distance_m, default=0) > MAX_DISTANCE_TO_CITY_M:
        raise ValueError(f"A school lies more than {MAX_DISTANCE_TO_CITY_M} m from its address city")
    return study


def main() -> None:
    for path in (SCHOOLS_PATH, PLACES_PATH):
        if not path.exists():
            raise FileNotFoundError(f"{path} — run scripts/download_data.py first")

    schools = gpd.read_file(SCHOOLS_PATH)
    print("Schools read:", len(schools))
    cities = select_city_boundaries(gpd.read_file(PLACES_PATH))
    study = add_flags(filter_schools(schools), cities)

    print("Schools written:", len(study))
    print(study.groupby(["City", "in_city_limits"]).size().to_string())
    print("Not proximity eligible (Virtual = V):", (~study["proximity_eligible"]).sum())

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.unlink(missing_ok=True)
    study.to_file(OUTPUT_PATH, layer="schools", driver="GPKG")
    cities.to_file(OUTPUT_PATH, layer="city_boundaries", driver="GPKG")
    print("Output:", OUTPUT_PATH.relative_to(ROOT), "| CRS:", WORKING_CRS)


if __name__ == "__main__":
    main()
