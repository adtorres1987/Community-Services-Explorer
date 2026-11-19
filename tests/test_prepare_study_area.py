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


def write_dhc_files(tmp_path, blocks):
    """Minimal DHC geographic header and segment 6 for (sumlev, geocode, P12 cells) records."""
    geo_lines, segment_lines = [], []
    for logrecno, (sumlev, geocode, p12) in enumerate(blocks, start=1):
        geo = [""] * 97
        geo[ps.DHC_SUMLEV], geo[ps.DHC_LOGRECNO], geo[ps.DHC_GEOCODE] = sumlev, f"{logrecno:07d}", geocode
        geo_lines.append("|".join(geo))
        segment = ["DHCST", "CA", "000", "06", f"{logrecno:07d}"] + ["0"] * (71 + 73) + [str(v) for v in p12]
        segment += ["0"] * 49  # P12A
        segment_lines.append("|".join(segment))
    geo_path, segment_path = tmp_path / "geo.dhc", tmp_path / "seg6.dhc"
    geo_path.write_text("\n".join(geo_lines) + "\n", encoding="latin-1")
    segment_path.write_text("\n".join(segment_lines) + "\n", encoding="latin-1")
    return geo_path, segment_path


def p12(**ages):
    """P12 cells (49) from male/female counts per cell number, e.g. p12(m4=2, f30=1, m20=5)."""
    cells = [0] * 49
    for key, count in ages.items():
        cells[int(key[1:]) - 1] = count
    cells[1] = sum(cells[2:25])  # male total
    cells[25] = sum(cells[26:49])  # female total
    cells[0] = cells[1] + cells[25]
    return cells


def test_read_block_age_5_17_sums_school_age_cells(tmp_path):
    geo, segment = write_dhc_files(tmp_path, [
        ("050", "06071", p12(m4=99)),  # county summary, not a block
        # 5-9, 10-14, 15-17 for both sexes count; under 5 (3, 27) and 18-19 (7, 31) do not
        ("100", "060710001001000", p12(m3=1, m4=2, m5=3, m6=4, m7=5, f27=1, f28=6, f29=7, f30=8, f31=9)),
        ("100", "060710001001001", p12(m20=10)),
        ("100", "060650001001000", p12(m4=50)),  # another county
    ])
    assert ps.read_block_age_5_17(geo, segment, "06071").to_dict("records") == [
        {"GEOID20": "060710001001000", "population_5_17": 30},
        {"GEOID20": "060710001001001", "population_5_17": 0},
    ]


def test_read_block_age_5_17_rejects_inconsistent_records(tmp_path):
    cells = p12(m4=2)
    cells[0] += 1  # total no longer equals male + female
    geo, segment = write_dhc_files(tmp_path, [("100", "060710001001000", cells)])
    with pytest.raises(ValueError, match="Inconsistent P12"):
        ps.read_block_age_5_17(geo, segment, "06071")


def test_read_block_age_5_17_requires_every_block(tmp_path):
    geo, segment = write_dhc_files(tmp_path, [("100", "060710001001000", p12(m4=2))])
    with geo.open("a", encoding="latin-1") as f:
        extra = [""] * 97
        extra[ps.DHC_SUMLEV], extra[ps.DHC_LOGRECNO], extra[ps.DHC_GEOCODE] = "100", "0000002", "060710001001001"
        f.write("|".join(extra) + "\n")
    with pytest.raises(ValueError, match="1 of 2 blocks"):
        ps.read_block_age_5_17(geo, segment, "06071")


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
    population = pd.DataFrame({
        "GEOID20": ["inside", "split", "outside"],
        "population": [100, 80, 40],
        "population_5_17": [20, 10, 8],
    })

    units = ps.apportion_population(blocks, population, cities)
    totals = units.groupby(["geoid20", "city"])[["population", "population_5_17"]].sum().round(6)
    assert totals.to_dict("index") == {
        ("inside", "Alpha"): {"population": 100, "population_5_17": 20},
        ("split", "Alpha"): {"population": 40, "population_5_17": 5},
        ("split", "Beta"): {"population": 40, "population_5_17": 5},
    }


def test_apportion_population_requires_every_block():
    cities = ps.select_city_boundaries(make_places())
    blocks = gpd.GeoDataFrame(
        {"GEOID20": ["a"], "geometry": [box(480_500, 3_768_500, 481_000, 3_769_000)]}, crs="EPSG:26911"
    )
    with pytest.raises(ValueError, match="without population"):
        ps.apportion_population(blocks, pd.DataFrame({"GEOID20": ["b"], "population": [1]}), cities)


def outlet(seq, x, y, **overrides):
    """PLS outlet record (strings, as read from the CSV) at UTM x, y."""
    lon_lat = gpd.GeoSeries([Point(x, y)], crs="EPSG:26911").to_crs("EPSG:4326").iloc[0]
    row = {
        "STABR": "CA", "FSCSKEY": "CA0001", "FSCS_SEQ": seq, "C_FSCS": "Y", "C_OUT_TY": "BR",
        "STATSTRU": "00", "LIBNAME": f"BRANCH {seq} LIBRARY", "ADDRESS": "1 MAIN ST.",
        "CITY": "ALPHA", "ZIP": "92373", "PHONE": "9095550100", "SQ_FEET": "5000",
        "HOURS": "1776", "WKS_OPEN": "52", "LONGITUD": str(lon_lat.x), "LATITUDE": str(lon_lat.y),
    }
    row.update(overrides)
    return row


SYSTEMS = pd.DataFrame([
    {"FSCSKEY": "CA0001", "LIBNAME": "ALPHA COUNTY LIBRARY"},
    {"FSCSKEY": "CA0002", "LIBNAME": "LAW LIBRARY FOR ALPHA COUNTY"},
])


def test_select_libraries_keeps_public_fixed_open_outlets():
    cities = ps.select_city_boundaries(make_places())
    outlets = pd.DataFrame([
        outlet("001", 481_000, 3_769_000, C_OUT_TY="CE", LIBNAME="ALPHA MAIN LIBRARY"),
        outlet("002", 483_000, 3_769_000, SQ_FEET="-1"),  # in Beta; missing size
        outlet("003", 486_000, 3_769_000),  # 2 km outside: context
        outlet("004", 490_000, 3_769_000),  # 6 km outside: dropped
        outlet("005", 481_500, 3_769_000, C_OUT_TY="BS"),  # bookmobile
        outlet("006", 481_500, 3_768_500, STATSTRU="23"),  # temporarily closed
        outlet("001", 481_200, 3_769_200, FSCSKEY="CA0002", C_FSCS="N"),  # law library
        outlet("007", 481_000, 3_769_500, STABR="NV"),
    ])
    libraries = ps.select_libraries(outlets, SYSTEMS, cities).set_index("library_id")

    assert list(libraries.index) == ["CA0001-001", "CA0001-002", "CA0001-003"]
    assert libraries["study_city"].tolist() == ["Alpha", "Beta", None]
    assert libraries["in_study_area"].tolist() == [True, True, False]
    assert libraries["proximity_eligible"].all()
    main = libraries.loc["CA0001-001"]
    assert (main["name"], main["outlet_type"], main["system"]) == (
        "Alpha Main Library", "Central", "Alpha County Library",
    )
    assert (main["address"], main["address_city"], main["square_feet"]) == ("1 Main St.", "Alpha", 5000)
    assert pd.isna(libraries.loc["CA0001-002", "square_feet"])
    assert libraries.crs.to_epsg() == 26911
    assert libraries.loc["CA0001-001", "geometry"].distance(Point(481_000, 3_769_000)) < 0.01


def test_select_libraries_context_distance_is_two_miles():
    cities = ps.select_city_boundaries(make_places())
    outlets = pd.DataFrame([
        outlet("001", 484_000 + 3_150, 3_769_000),
        outlet("002", 484_000 + 3_250, 3_769_000),
    ])
    libraries = ps.select_libraries(outlets, SYSTEMS, cities)
    assert libraries["library_id"].tolist() == ["CA0001-001"]


def test_select_libraries_rejects_duplicates_and_missing_coordinates():
    cities = ps.select_city_boundaries(make_places())
    with pytest.raises(ValueError, match="Duplicate"):
        ps.select_libraries(
            pd.DataFrame([outlet("001", 481_000, 3_769_000)] * 2), SYSTEMS, cities
        )
    with pytest.raises(ValueError, match="without coordinates"):
        ps.select_libraries(
            pd.DataFrame([outlet("001", 481_000, 3_769_000, LATITUDE="")]), SYSTEMS, cities
        )


def test_display_case_keeps_short_words_lower_case():
    assert ps.display_case("MENTONE SENIOR CENTER AND LIBRARY") == "Mentone Senior Center and Library"
    assert ps.display_case("656 N. 9TH ST.") == "656 N. 9th St."
    assert ps.display_case(None) is None


def make_gtfs(stops, stop_times, routes=None, calendar=None, calendar_dates=None):
    """Synthetic GTFS tables (text, as read_gtfs returns them)."""
    routes = routes or [
        {"route_id": "r1", "route_short_name": "15", "route_long_name": "Fifteen", "route_type": "3"},
        {"route_id": "r2", "route_short_name": "", "route_long_name": "sbX Green Line", "route_type": "3"},
        {"route_id": "dr", "route_short_name": "OR", "route_long_name": "OmniRide", "route_type": "715"},
    ]
    calendar = calendar or [
        {"service_id": "wk", "monday": "1", "tuesday": "1", "wednesday": "1", "thursday": "1",
         "friday": "1", "saturday": "0", "sunday": "0", "start_date": "20260801", "end_date": "20261231"},
        {"service_id": "sat", "monday": "0", "tuesday": "0", "wednesday": "0", "thursday": "0",
         "friday": "0", "saturday": "1", "sunday": "0", "start_date": "20260801", "end_date": "20261231"},
    ]
    trips = sorted({(t["trip_id"], t["route_id"], t["service_id"]) for t in stop_times})
    tables = {
        "stops": pd.DataFrame(stops).fillna(""),
        "routes": pd.DataFrame(routes),
        "trips": pd.DataFrame(trips, columns=["trip_id", "route_id", "service_id"]),
        "stop_times": pd.DataFrame(
            [{k: v for k, v in t.items() if k not in ("route_id", "service_id")} for t in stop_times]
        ).fillna(""),
        "calendar": pd.DataFrame(calendar),
    }
    if calendar_dates:
        tables["calendar_dates"] = pd.DataFrame(calendar_dates)
    return tables


def departures(stop_id, times, route_id="r1", service_id="wk", prefix="t", pickup_type="0"):
    return [
        {"trip_id": f"{prefix}{i}", "stop_id": stop_id, "departure_time": time, "route_id": route_id,
         "service_id": service_id, "pickup_type": pickup_type}
        for i, time in enumerate(times)
    ]


def test_active_services_applies_calendar_dates():
    gtfs = make_gtfs([], [], calendar_dates=[
        {"service_id": "wk", "date": "20260907", "exception_type": "2"},  # Labor Day
        {"service_id": "sat", "date": "20260907", "exception_type": "1"},
    ])
    assert ps.active_services(gtfs, "20260916") == {"wk"}
    assert ps.active_services(gtfs, "20260907") == {"sat"}
    assert ps.active_services(gtfs, "20270201") == set()


def test_stop_service_counts_weekday_pickups_and_am_peak():
    stop_times = (
        departures("a", ["06:50:00", "07:00:00", "07:15:00", "07:30:00", "08:45:00", "09:00:00"])
        + departures("a", ["07:05:00", "08:05:00"], route_id="r2", prefix="x")
        + departures("a", ["07:10:00"], service_id="sat", prefix="s")  # not on the weekday
        + departures("a", ["07:20:00"], route_id="dr", prefix="d")  # demand responsive
        + departures("a", ["07:40:00"], prefix="n", pickup_type="1")  # drop-off only
        + departures("b", ["25:10:00"], prefix="late")  # after midnight
    )
    summary = ps.stop_service(make_gtfs([], stop_times), "20260916")
    a = summary.loc["a"]
    assert a["weekday_departures"] == 8
    # 6 departures between 07:00 and 08:59 over two hours
    assert a["peak_departures_per_hour"] == 3.0
    assert a["routes"] == "15, sbX Green Line"
    assert summary.loc["b", "peak_departures_per_hour"] == 0


def test_service_class_thresholds():
    assert ps.service_class(40, 4.0, "Bus") == ps.TRANSIT_FREQUENT
    assert ps.service_class(40, 3.5, "Bus") == ps.TRANSIT_MEDIUM
    assert ps.service_class(40, 2.0, "Bus") == ps.TRANSIT_MEDIUM
    assert ps.service_class(10, 0.0, "Bus") == ps.TRANSIT_INFREQUENT
    assert ps.service_class(30, 1.5, "Rail") == ps.TRANSIT_RAIL
    assert ps.service_class(0, 0.0, "Rail") == ps.TRANSIT_NO_SERVICE


def stop(stop_id, x, y, location_type="0", wheelchair="1"):
    lon_lat = gpd.GeoSeries([Point(x, y)], crs="EPSG:26911").to_crs("EPSG:4326").iloc[0]
    return {"stop_id": stop_id, "stop_name": f"Stop {stop_id}", "stop_lat": str(lon_lat.y),
            "stop_lon": str(lon_lat.x), "location_type": location_type, "wheelchair_boarding": wheelchair}


def test_select_transit_stops_classifies_and_keeps_context():
    cities = ps.select_city_boundaries(make_places())
    bus = make_gtfs(
        [
            stop("1", 481_000, 3_769_000),  # Alpha, frequent
            stop("2", 483_000, 3_769_000, wheelchair="0"),  # Beta, no service
            stop("3", 484_700, 3_769_000),  # 700 m outside: context
            stop("4", 485_000, 3_769_000),  # 1 km outside: dropped
            stop("S", 481_000, 3_769_000, location_type="1"),  # parent station
        ],
        departures("1", [f"07:{m:02d}:00" for m in range(0, 60, 10)] + [f"08:{m:02d}:00" for m in range(0, 60, 10)])
        + departures("3", ["12:00:00"], prefix="c")
        + departures("4", ["07:00:00"], prefix="f"),
    )
    rail = make_gtfs(
        [{"stop_id": "9", "stop_name": "Alpha Station", **{k: v for k, v in stop("9", 481_500, 3_768_500).items() if k.startswith("stop_l")}}],
        departures("9", ["07:30:00"], prefix="m"),
    )
    stops = ps.select_transit_stops([(bus, "Bus Co", "Bus"), (rail, "Rail Co", "Rail")], cities, "20260916")
    stops = stops.set_index("stop_key")

    assert sorted(stops.index) == ["bus co:1", "bus co:2", "bus co:3", "rail co:9"]
    assert stops.loc["bus co:1", "service_class"] == ps.TRANSIT_FREQUENT
    assert stops.loc["bus co:1", "peak_departures_per_hour"] == 6.0
    assert stops.loc["bus co:2", "service_class"] == ps.TRANSIT_NO_SERVICE
    assert not stops.loc["bus co:2", "proximity_eligible"]
    assert pd.isna(stops.loc["bus co:2", "wheelchair_boarding"])
    assert stops.loc["bus co:1", "wheelchair_boarding"] == "Yes"
    assert stops.loc["bus co:3", "study_city"] is None
    assert stops.loc["rail co:9", ["service_class", "study_city"]].tolist() == [ps.TRANSIT_RAIL, "Alpha"]
    assert stops["in_study_area"].tolist() == [True, True, False, True]
