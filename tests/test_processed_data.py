"""Checks on the committed data/processed/study_area.gpkg (the dataset the app loads)."""
import geopandas as gpd
import pyogrio
import pytest

import prepare_schools as ps


@pytest.fixture(scope="module")
def schools():
    return gpd.read_file(ps.OUTPUT_PATH, layer="schools")


@pytest.fixture(scope="module")
def cities():
    return gpd.read_file(ps.OUTPUT_PATH, layer="city_boundaries")


def test_layers():
    layers = dict(pyogrio.list_layers(ps.OUTPUT_PATH))
    assert layers == {"schools": "Point", "city_boundaries": "MultiPolygon"}


def test_crs(schools, cities):
    assert schools.crs.to_epsg() == 26911
    assert cities.crs.to_epsg() == 26911


def test_documented_counts(schools):
    # Values documented in docs/data-sources.md
    assert len(schools) == 37
    assert schools.groupby("City").size().to_dict() == {"Redlands": 24, "Yucaipa": 13}
    assert schools["in_city_limits"].sum() == 35
    assert schools["proximity_eligible"].sum() == 33
    assert set(schools.loc[~schools["in_city_limits"], "SchoolName"]) == {
        "Mission Elementary",
        "Redlands East Valley High",
    }


def test_records_are_valid(schools, cities):
    assert schools["CDSCode"].is_unique
    assert (schools["Status"] == "Active").all()
    assert schools.is_valid.all() and not schools.geometry.is_empty.any()
    assert cities.is_valid.all()


def test_points_match_source_coordinates(schools):
    # Geometry must agree with the source Latitude/Longitude attributes (to ~1 m)
    wgs84 = schools.to_crs("EPSG:4326").geometry
    assert ((wgs84.x - schools["Longitude"]).abs() < 1e-5).all()
    assert ((wgs84.y - schools["Latitude"]).abs() < 1e-5).all()
