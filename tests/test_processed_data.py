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
POPULATION_5_17_BY_PLACE = {
    "Colton": 10689, "Grand Terrace": 2129, "Highland": 11893, "Loma Linda": 3550,
    "Mentone": 1712, "Redlands": 12118, "Rialto": 21785, "San Bernardino": 46869,
    "Yucaipa": 9724,
}


@pytest.fixture(scope="module")
def schools():
    return gpd.read_file(ps.OUTPUT_PATH, layer="schools")


LIBRARIES_BY_PLACE = {
    "Colton": 2, "Grand Terrace": 1, "Highland": 1, "Loma Linda": 1, "Mentone": 1,
    "Redlands": 1, "Rialto": 2, "San Bernardino": 4, "Yucaipa": 1,
}


TRANSIT_STOPS_BY_PLACE = {
    "Colton": 93, "Grand Terrace": 13, "Highland": 71, "Loma Linda": 55, "Mentone": 20,
    "Redlands": 99, "Rialto": 197, "San Bernardino": 554, "Yucaipa": 60,
}


@pytest.fixture(scope="module")
def transit_stops():
    return gpd.read_file(ps.OUTPUT_PATH, layer="transit_stops")


@pytest.fixture(scope="module")
def libraries():
    return gpd.read_file(ps.OUTPUT_PATH, layer="libraries")


@pytest.fixture(scope="module")
def cities():
    return gpd.read_file(ps.OUTPUT_PATH, layer="city_boundaries")


@pytest.fixture(scope="module")
def units():
    return gpd.read_file(ps.OUTPUT_PATH, layer="population_units")


def test_layers():
    layers = dict(pyogrio.list_layers(ps.OUTPUT_PATH))
    assert layers == {
        "schools": "Point",
        "libraries": "Point",
        "transit_stops": "Point",
        "city_boundaries": "MultiPolygon",
        "population_units": "MultiPolygon",
    }


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
    assert (distance <= ps.SCHOOL_CONTEXT_DISTANCE_M).all()


def test_library_counts(libraries, cities):
    study = libraries[libraries["in_study_area"]]
    assert study.groupby("study_city").size().to_dict() == LIBRARIES_BY_PLACE
    assert len(libraries) == 20
    assert libraries["library_id"].is_unique
    assert libraries["proximity_eligible"].all()
    assert set(libraries["outlet_type"]) == {"Central", "Branch"}
    # County law libraries do not meet the public library definition (C_FSCS = N)
    assert not libraries["name"].str.contains("Law Library").any()
    context = libraries[~libraries["in_study_area"]]
    distance = context.geometry.distance(cities.union_all())
    assert ((distance > 0) & (distance <= ps.LIBRARY_CONTEXT_DISTANCE_M)).all()


def test_transit_stops(transit_stops, cities):
    study = transit_stops[transit_stops["in_study_area"]]
    assert study.groupby("study_city").size().to_dict() == TRANSIT_STOPS_BY_PLACE
    assert study["service_class"].value_counts().to_dict() == {
        ps.TRANSIT_INFREQUENT: 472, ps.TRANSIT_MEDIUM: 445, ps.TRANSIT_FREQUENT: 238, ps.TRANSIT_RAIL: 7,
    }
    assert len(transit_stops) == 1249
    assert transit_stops["stop_key"].is_unique
    assert transit_stops["proximity_eligible"].all()
    assert set(study.loc[study["mode"] == "Rail", "name"]) == {
        "Redlands - Downtown", "Redlands - Esri", "Redlands - University", "Rialto",
        "San Bernardino - Downtown", "San Bernardino - Tippecanoe", "San Bernardino Depot",
    }
    context = transit_stops[~transit_stops["in_study_area"]]
    distance = context.geometry.distance(cities.union_all())
    assert ((distance > 0) & (distance <= ps.TRANSIT_CONTEXT_DISTANCE_M)).all()
    wgs84 = transit_stops.to_crs("EPSG:4326").geometry
    assert ((wgs84.x - transit_stops["stop_lon"]).abs() < 1e-5).all()
    assert ((wgs84.y - transit_stops["stop_lat"]).abs() < 1e-5).all()


def test_library_points_match_source_coordinates(libraries):
    wgs84 = libraries.to_crs("EPSG:4326").geometry
    assert ((wgs84.x - libraries["LONGITUD"]).abs() < 1e-5).all()
    assert ((wgs84.y - libraries["LATITUDE"]).abs() < 1e-5).all()


def test_population(cities, units):
    assert dict(zip(cities["city"], cities["population"])) == POPULATION_BY_PLACE
    by_place = units.groupby("city")["population"].sum().round().astype(int).to_dict()
    assert by_place == POPULATION_BY_PLACE


def test_population_5_17(cities, units):
    assert dict(zip(cities["city"], cities["population_5_17"])) == POPULATION_5_17_BY_PLACE
    by_place = units.groupby("city")["population_5_17"].sum().round().astype(int).to_dict()
    assert by_place == POPULATION_5_17_BY_PLACE
    assert (units["population_5_17"] >= 0).all()
    assert (units["population_5_17"] <= units["population"] + 1e-9).all()


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
