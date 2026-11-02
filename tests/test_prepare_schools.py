"""Unit tests for scripts/prepare_schools.py using small synthetic datasets."""
import geopandas as gpd
import pytest
from shapely.geometry import Point, box

import prepare_schools as ps

# Two square "cities" in EPSG:26911 (metres), roughly where the real ones are
REDLANDS = box(480_000, 3_768_000, 482_000, 3_770_000)
YUCAIPA = box(492_000, 3_765_000, 494_000, 3_767_000)


def make_places(extra=()):
    rows = [
        {"GEOID": "0659962", "NAME": "Redlands", "NAMELSAD": "Redlands city", "LSAD": "25", "geometry": REDLANDS},
        {"GEOID": "0687042", "NAME": "Yucaipa", "NAMELSAD": "Yucaipa city", "LSAD": "25", "geometry": YUCAIPA},
        *extra,
    ]
    return gpd.GeoDataFrame(rows, crs="EPSG:26911").to_crs("EPSG:4269")


def school(cds, city, x, y, status="Active", virtual="N"):
    row = {column: None for column in ps.KEEP_COLUMNS}
    row.update(CDSCode=cds, SchoolName=f"School {cds}", City=city, Status=status, Virtual=virtual)
    row["geometry"] = Point(x, y)
    return row


def make_schools(rows):
    return gpd.GeoDataFrame(rows, crs="EPSG:26911").to_crs(ps.SOURCE_CRS)


def test_select_city_boundaries_keeps_incorporated_cities():
    # A census-designated place (LSAD 57) with the same name must be ignored
    cdp = {"GEOID": "0699999", "NAME": "Redlands", "NAMELSAD": "Redlands CDP", "LSAD": "57", "geometry": YUCAIPA}
    cities = ps.select_city_boundaries(make_places([cdp]))
    assert sorted(cities["city"]) == ["Redlands", "Yucaipa"]
    assert cities.crs.to_epsg() == 26911
    assert list(cities.columns) == ["geoid", "city", "name_lsad", "geometry"]


def test_select_city_boundaries_requires_both_cities():
    places = make_places()
    with pytest.raises(ValueError, match="one boundary per city"):
        ps.select_city_boundaries(places[places["NAME"] == "Redlands"])


def test_filter_schools_keeps_active_schools_in_study_cities():
    schools = make_schools([
        school("1", "Redlands", 481_000, 3_769_000),
        school("2", "Yucaipa", 493_000, 3_766_000),
        school("3", "Highland", 481_000, 3_772_000),
        school("4", "Redlands", 481_500, 3_769_500, status="Closed"),
    ])
    study = ps.filter_schools(schools)
    assert sorted(study["CDSCode"]) == ["1", "2"]
    assert study.crs.to_epsg() == 26911
    assert list(study.columns) == ps.KEEP_COLUMNS + ["geometry"]


def test_filter_schools_rejects_unexpected_crs():
    schools = make_schools([school("1", "Redlands", 481_000, 3_769_000)]).to_crs("EPSG:4326")
    with pytest.raises(ValueError, match="Unexpected schools CRS"):
        ps.filter_schools(schools)


def test_filter_schools_rejects_duplicate_ids():
    schools = make_schools([
        school("1", "Redlands", 481_000, 3_769_000),
        school("1", "Yucaipa", 493_000, 3_766_000),
    ])
    with pytest.raises(ValueError, match="Duplicate CDSCode"):
        ps.filter_schools(schools)


def test_filter_schools_rejects_empty_geometry():
    schools = make_schools([school("1", "Redlands", 481_000, 3_769_000)])
    schools.loc[0, "geometry"] = Point()
    with pytest.raises(ValueError, match="Invalid school geometries"):
        ps.filter_schools(schools)


def test_add_flags():
    cities = ps.select_city_boundaries(make_places())
    study = ps.filter_schools(make_schools([
        school("inside", "Redlands", 481_000, 3_769_000),
        school("outside", "Redlands", 482_100, 3_769_000),  # 100 m east of the boundary
        school("virtual", "Yucaipa", 493_000, 3_766_000, virtual="V"),
    ]))
    flagged = ps.add_flags(study, cities).set_index("CDSCode")
    assert flagged["in_city_limits"].to_dict() == {"inside": True, "outside": False, "virtual": True}
    assert flagged["proximity_eligible"].to_dict() == {"inside": True, "outside": True, "virtual": False}


def test_add_flags_rejects_school_far_from_its_city():
    cities = ps.select_city_boundaries(make_places())
    # Address says Redlands but the point is in Yucaipa, ~10 km away
    study = ps.filter_schools(make_schools([school("1", "Redlands", 493_000, 3_766_000)]))
    with pytest.raises(ValueError, match="more than"):
        ps.add_flags(study, cities)
