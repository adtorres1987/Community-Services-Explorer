"""Checks on the committed data/processed/study_area.gpkg (the dataset the app loads)."""
import geopandas as gpd
import pyogrio
import pytest

import prepare_study_area as ps

# Values documented in docs/data-sources.md
SCHOOLS_BY_PLACE = {
    "Colton": 15, "Grand Terrace": 4, "Highland": 10, "Loma Linda": 2, "Mentone": 2,
    "Redlands": 22, "Rialto": 28, "San Bernardino": 77, "Yucaipa": 13,
}
POPULATION_BY_PLACE = {
    "Colton": 53915, "Grand Terrace": 13148, "Highland": 56969, "Loma Linda": 24939,
    "Mentone": 9557, "Redlands": 73161, "Rialto": 104063, "San Bernardino": 222042,
    "Yucaipa": 54541,
}


@pytest.fixture(scope="module")
def schools():
    return gpd.read_file(ps.OUTPUT_PATH, layer="schools")


@pytest.fixture(scope="module")
def cities():
    return gpd.read_file(ps.OUTPUT_PATH, layer="city_boundaries")


@pytest.fixture(scope="module")
def units():
    return gpd.read_file(ps.OUTPUT_PATH, layer="population_units")


def test_layers():
    layers = dict(pyogrio.list_layers(ps.OUTPUT_PATH))
    assert layers == {"schools": "Point", "city_boundaries": "MultiPolygon", "population_units": "MultiPolygon"}


def test_crs(schools, cities, units):
    for layer in (schools, cities, units):
        assert layer.crs.to_epsg() == 26911


def test_school_counts(schools):
    assert len(schools) == 205
    study = schools[schools["in_study_area"]]
    assert study.groupby("study_city").size().to_dict() == SCHOOLS_BY_PLACE
    assert schools["study_city"].isna().sum() == 32
    assert (~schools["proximity_eligible"]).sum() == 7


def test_context_schools_are_near_the_study_area(schools, cities):
    context = schools[~schools["in_study_area"]]
    distance = context.geometry.distance(cities.union_all())
    assert (distance > 0).all()
    assert (distance <= ps.CONTEXT_DISTANCE_M).all()


def test_population(cities, units):
    assert dict(zip(cities["city"], cities["population"])) == POPULATION_BY_PLACE
    by_place = units.groupby("city")["population"].sum().round().astype(int).to_dict()
    assert by_place == POPULATION_BY_PLACE


def test_records_are_valid(schools, cities, units):
    assert schools["CDSCode"].is_unique
    assert (schools["Status"] == "Active").all()
    assert schools.is_valid.all() and not schools.geometry.is_empty.any()
    assert cities.is_valid.all()
    assert units.is_valid.all() and (units.area > 0).all()


def test_points_match_source_coordinates(schools):
    # Geometry must agree with the source Latitude/Longitude attributes (to ~1 m)
    wgs84 = schools.to_crs("EPSG:4326").geometry
    assert ((wgs84.x - schools["Longitude"]).abs() < 1e-5).all()
    assert ((wgs84.y - schools["Latitude"]).abs() < 1e-5).all()
