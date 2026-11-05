"""Unit tests for scripts/prepare_study_area.py using small synthetic datasets."""
import geopandas as gpd
import pandas as pd
import pytest
from shapely.geometry import Point, box

import prepare_study_area as ps

# Two adjacent square "places" in EPSG:26911 (metres)
ALPHA = box(480_000, 3_768_000, 482_000, 3_770_000)
BETA = box(482_000, 3_768_000, 484_000, 3_770_000)
PLACES = {"0600001": "Alpha", "0600002": "Beta"}


@pytest.fixture(autouse=True)
def study_places(monkeypatch):
    monkeypatch.setattr(ps, "STUDY_PLACES", PLACES)


def make_places(extra=()):
    rows = [
        {"GEOID": "0600001", "NAME": "Alpha", "NAMELSAD": "Alpha city", "LSAD": "25", "geometry": ALPHA},
        {"GEOID": "0600002", "NAME": "Beta", "NAMELSAD": "Beta CDP", "LSAD": "57", "geometry": BETA},
        *extra,
    ]
    return gpd.GeoDataFrame(rows, crs="EPSG:26911").to_crs("EPSG:4269")


def school(cds, x, y, status="Active", virtual="N", address_city="Alpha"):
    row = {column: None for column in ps.KEEP_COLUMNS}
    row.update(CDSCode=cds, SchoolName=f"School {cds}", City=address_city, Status=status, Virtual=virtual)
    row["geometry"] = Point(x, y)
    return row


def make_schools(rows):
    return gpd.GeoDataFrame(rows, crs="EPSG:26911").to_crs(ps.SOURCE_CRS)


def test_select_city_boundaries_by_geoid():
    # A place elsewhere with the same name must be ignored
    namesake = {"GEOID": "0699999", "NAME": "Alpha", "NAMELSAD": "Alpha CDP", "LSAD": "57", "geometry": BETA}
    cities = ps.select_city_boundaries(make_places([namesake]))
    assert sorted(cities["city"]) == ["Alpha", "Beta"]
    assert cities.crs.to_epsg() == 26911
    assert list(cities.columns) == ["geoid", "city", "name_lsad", "lsad", "geometry"]


def test_select_city_boundaries_requires_all_places():
    places = make_places()
    with pytest.raises(ValueError, match="Expected places"):
        ps.select_city_boundaries(places[places["NAME"] == "Alpha"])


def test_select_schools_assigns_by_boundary_and_keeps_nearby_context():
    cities = ps.select_city_boundaries(make_places())
    selected = ps.select_schools(
        make_schools([
            # Address says Alpha, but the school is inside Beta
            school("in-beta", 483_000, 3_769_000, address_city="Alpha"),
            school("in-alpha", 481_000, 3_769_000),
            school("near", 481_000, 3_771_500),  # 1.5 km north of Alpha
            school("far", 481_000, 3_775_000),  # 5 km away
            school("closed", 481_500, 3_769_500, status="Closed"),
            school("virtual", 481_200, 3_769_200, virtual="V"),
        ]),
        cities,
    ).set_index("CDSCode")

    assert sorted(selected.index) == ["in-alpha", "in-beta", "near", "virtual"]
    assert selected.loc["in-beta", "study_city"] == "Beta"
    assert selected.loc["in-beta", "City"] == "Alpha"
    assert selected["in_study_area"].to_dict() == {
        "in-beta": True, "in-alpha": True, "near": False, "virtual": True,
    }
    assert selected.loc["near", "study_city"] is None
    assert selected["proximity_eligible"].to_dict() == {
        "in-beta": True, "in-alpha": True, "near": True, "virtual": False,
    }
    assert selected.crs.to_epsg() == 26911


def test_select_schools_rejects_unexpected_crs():
    cities = ps.select_city_boundaries(make_places())
    schools = make_schools([school("1", 481_000, 3_769_000)]).to_crs("EPSG:4326")
    with pytest.raises(ValueError, match="Unexpected schools CRS"):
        ps.select_schools(schools, cities)


def test_select_schools_rejects_duplicate_ids():
    cities = ps.select_city_boundaries(make_places())
    schools = make_schools([school("1", 481_000, 3_769_000), school("1", 483_000, 3_769_000)])
    with pytest.raises(ValueError, match="Duplicate CDSCode"):
        ps.select_schools(schools, cities)


def test_select_schools_rejects_empty_geometry():
    cities = ps.select_city_boundaries(make_places())
    schools = make_schools([school("1", 481_000, 3_769_000)])
    schools.loc[0, "geometry"] = Point()
    with pytest.raises(ValueError, match="Invalid school geometries"):
        ps.select_schools(schools, cities)


def write_pl_header(path, rows):
    """Minimal P.L. 94-171 geographic header: 97 pipe-delimited fields per record."""
    lines = []
    for sumlev, geocode, population in rows:
        fields = [""] * 97
        fields[ps.PL_SUMLEV], fields[ps.PL_GEOCODE], fields[ps.PL_POP100] = sumlev, geocode, str(population)
        lines.append("|".join(fields))
    path.write_text("\n".join(lines) + "\n", encoding="latin-1")


def test_read_block_population_keeps_county_blocks(tmp_path):
    path = tmp_path / "geo.pl"
    write_pl_header(path, [
        ("050", "06071", 999),  # county summary, not a block
        ("750", "060710001001000", 10),
        ("750", "060710001001001", 0),
        ("750", "060650001001000", 50),  # another county
    ])
    population = ps.read_block_population(path, "06071")
    assert population.to_dict("records") == [
        {"GEOID20": "060710001001000", "population": 10},
        {"GEOID20": "060710001001001", "population": 0},
    ]


def test_apportion_population_by_area():
    cities = ps.select_city_boundaries(make_places())
    blocks = gpd.GeoDataFrame(
        {
            "GEOID20": ["inside", "split", "outside"],
            # inside Alpha; half in Alpha, half in Beta; outside both
            "geometry": [
                box(480_500, 3_768_500, 481_000, 3_769_000),
                box(481_500, 3_768_500, 482_500, 3_769_000),
                box(490_000, 3_768_000, 491_000, 3_769_000),
            ],
        },
        crs="EPSG:26911",
    ).to_crs("EPSG:4269")
    population = pd.DataFrame({"GEOID20": ["inside", "split", "outside"], "population": [100, 80, 40]})

    units = ps.apportion_population(blocks, population, cities)
    totals = units.groupby(["geoid20", "city"])["population"].sum().round(6).to_dict()
    assert totals == {("inside", "Alpha"): 100, ("split", "Alpha"): 40, ("split", "Beta"): 40}


def test_apportion_population_requires_every_block():
    cities = ps.select_city_boundaries(make_places())
    blocks = gpd.GeoDataFrame(
        {"GEOID20": ["a"], "geometry": [box(480_500, 3_768_500, 481_000, 3_769_000)]}, crs="EPSG:26911"
    )
    with pytest.raises(ValueError, match="without population"):
        ps.apportion_population(blocks, pd.DataFrame({"GEOID20": ["b"], "population": [1]}), cities)
