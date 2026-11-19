# Expected coverage values were verified independently with GeoPandas from
# data/processed/study_area.gpkg (see docs/database.md).
import pytest

SCHOOLS = {"facility_type": "school"}
LIBRARIES = {"facility_type": "library"}
TRANSIT = {"facility_type": "transit"}


@pytest.mark.parametrize(
    ("city", "radius_m", "area_pct", "population_pct", "age_5_17_pct", "contributing"),
    [
        ("Redlands", 500, 13.0, 24.2, 24.5, 21),
        ("Redlands", 1000, 39.6, 74.8, 76.4, 22),
        ("Yucaipa", 1000, 35.3, 59.4, 61.6, 15),
        ("San Bernardino", 1000, 58.2, 88.3, 89.2, 102),
        ("Mentone", 500, 10.5, 33.8, 34.3, 3),
        ("Loma Linda", 1000, 25.9, 28.7, 29.9, 5),
        ("Rialto", 1000, 65.7, 94.9, 95.1, 43),
        ("Colton", 500, 20.1, 37.7, 38.4, 18),
        ("Grand Terrace", 1000, 76.0, 90.4, 91.7, 5),
    ],
)
def test_coverage_matches_verified_values(
    client, city, radius_m, area_pct, population_pct, age_5_17_pct, contributing
):
    response = client.get("/analysis/proximity", params={"city": city, "radius_m": radius_m, **SCHOOLS})
    assert response.status_code == 200
    [result] = response.json()["results"]
    assert result["city"] == city
    assert result["covered_pct"] == area_pct
    assert result["covered_population_pct"] == population_pct
    assert result["covered_population_5_17_pct"] == age_5_17_pct
    assert result["contributing_facilities"] == contributing
    assert result["coverage"]["type"] in {"Polygon", "MultiPolygon"}


def test_all_places_and_virtual_exclusion(client):
    body = client.get("/analysis/proximity", params={"radius_m": 500, **SCHOOLS}).json()
    results = {r["city"]: r for r in body["results"]}
    assert set(results) == {
        "Colton", "Grand Terrace", "Highland", "Loma Linda", "Mentone",
        "Redlands", "Rialto", "San Bernardino", "Yucaipa",
    }
    # Four exclusively virtual schools in Redlands are not proximity eligible
    assert results["Redlands"]["eligible_facilities"] == 18
    assert results["Redlands"]["excluded_facilities"] == 4
    assert results["Yucaipa"]["eligible_facilities"] == 13
    assert "Straight-line" in body["method"]


def test_contributing_ids_allow_distinct_counts_across_places(client):
    results = {
        r["city"]: r
        for r in client.get("/analysis/proximity", params={"radius_m": 1000, **SCHOOLS}).json()["results"]
    }
    for result in results.values():
        assert len(result["contributing_facility_ids"]) == result["contributing_facilities"]
    # Schools near the Redlands / Loma Linda boundary contribute to both places
    redlands = set(results["Redlands"]["contributing_facility_ids"])
    loma_linda = set(results["Loma Linda"]["contributing_facility_ids"])
    assert redlands & loma_linda
    assert len(redlands | loma_linda) < len(redlands) + len(loma_linda)


def test_neighbouring_schools_add_coverage(client):
    # Yucaipa has 13 eligible schools of its own; two more nearby reach it at 1 km
    [result] = client.get(
        "/analysis/proximity", params={"city": "Yucaipa", "radius_m": 1000, **SCHOOLS}
    ).json()["results"]
    assert result["eligible_facilities"] == 13
    assert result["contributing_facilities"] == 15


def test_population_never_exceeds_total(client):
    body = client.get("/analysis/proximity", params={"radius_m": 2000, **SCHOOLS}).json()
    for result in body["results"]:
        assert 0 <= result["covered_population"] <= result["population"]
        assert 0 <= result["covered_population_pct"] <= 100
        assert 0 <= result["covered_population_5_17"] <= result["population_5_17"]
        assert result["population_5_17"] < result["population"]


def test_population_5_17_totals(client):
    # 2020 DHC table P12, ages 5-17 (verified independently with GeoPandas)
    results = client.get("/analysis/proximity", params={"radius_m": 1000, **SCHOOLS}).json()["results"]
    assert sum(r["population_5_17"] for r in results) == 120469
    assert sum(r["covered_population_5_17"] for r in results) == 101455


def test_type_without_facilities_has_no_coverage(client):
    body = client.get(
        "/analysis/proximity", params={"city": "Yucaipa", "radius_m": 500, "facility_type": "park"}
    ).json()
    [result] = body["results"]
    assert result["eligible_facilities"] == 0
    assert result["contributing_facilities"] == 0
    assert result["contributing_facility_ids"] == []
    assert result["covered_pct"] == 0
    assert result["covered_population"] == 0
    assert result["covered_population_5_17"] == 0
    assert result["coverage"] is None


def test_filter_by_subtype(client):
    body = client.get(
        "/analysis/proximity",
        params={"city": "Redlands", "radius_m": 1000, "facility_subtype": "High", **SCHOOLS},
    ).json()
    [result] = body["results"]
    assert body["facility_subtype"] == "High"
    assert result["eligible_facilities"] == 3
    assert result["contributing_facilities"] == 4
    assert result["covered_population_pct"] == 15.9


@pytest.mark.parametrize(
    ("city", "radius_m", "area_pct", "population_pct", "age_5_17_pct", "contributing"),
    [
        ("Loma Linda", 800, 8.6, 17.6, 15.0, 1),
        ("Grand Terrace", 800, 26.1, 31.7, 30.7, 2),
        ("Mentone", 1600, 23.9, 72.4, 74.6, 1),
        ("Redlands", 1600, 12.1, 29.1, 29.7, 3),
        ("San Bernardino", 1600, 20.0, 31.8, 33.6, 8),
        ("Rialto", 3200, 83.7, 96.8, 97.1, 8),
        ("Yucaipa", 3200, 45.3, 74.9, 76.9, 2),
        ("Highland", 3200, 35.2, 63.6, 67.6, 3),
    ],
)
def test_library_coverage_matches_verified_values(
    client, city, radius_m, area_pct, population_pct, age_5_17_pct, contributing
):
    params = {"city": city, "radius_m": radius_m, **LIBRARIES}
    [result] = client.get("/analysis/proximity", params=params).json()["results"]
    assert result["covered_pct"] == area_pct
    assert result["covered_population_pct"] == population_pct
    assert result["covered_population_5_17_pct"] == age_5_17_pct
    assert result["contributing_facilities"] == contributing
    assert result["excluded_facilities"] == 0


def test_library_totals_at_two_miles(client):
    # Context libraries up to 3.2 km away (Fontana, Bloomington, Muscoy, Calimesa,
    # Highgrove) contribute: 20 distinct libraries for 14 inside the study area
    results = client.get("/analysis/proximity", params={"radius_m": 3200, **LIBRARIES}).json()["results"]
    assert sum(r["eligible_facilities"] for r in results) == 14
    assert len({i for r in results for i in r["contributing_facility_ids"]}) == 20
    assert sum(r["covered_population"] for r in results) == 523161
    assert sum(r["covered_population_5_17"] for r in results) == 104430


@pytest.mark.parametrize(
    ("city", "radius_m", "area_pct", "population_pct", "age_5_17_pct", "contributing"),
    [
        ("Rialto", 400, 47.3, 68.4, 69.3, 234),
        ("Grand Terrace", 400, 21.7, 28.2, 24.7, 15),
        ("Redlands", 800, 33.9, 71.2, 72.5, 147),
        ("Yucaipa", 800, 37.2, 69.7, 72.1, 62),
        ("San Bernardino", 800, 65.6, 89.2, 90.3, 707),
    ],
)
def test_transit_coverage_matches_verified_values(
    client, city, radius_m, area_pct, population_pct, age_5_17_pct, contributing
):
    params = {"city": city, "radius_m": radius_m, **TRANSIT}
    [result] = client.get("/analysis/proximity", params=params).json()["results"]
    assert result["covered_pct"] == area_pct
    assert result["covered_population_pct"] == population_pct
    assert result["covered_population_5_17_pct"] == age_5_17_pct
    assert result["contributing_facilities"] == contributing


@pytest.mark.parametrize(
    ("subtype", "radius_m", "covered_population"),
    [
        (None, 400, 356380),
        (None, 800, 521647),
        ("Frequent bus (15 min or better)", 400, 107692),
        ("Frequent bus (15 min or better)", 800, 217204),
        ("Rail", 800, 21619),
    ],
)
def test_transit_totals_by_service_level(client, subtype, radius_m, covered_population):
    params = {"radius_m": radius_m, **TRANSIT}
    if subtype:
        params["facility_subtype"] = subtype
    results = client.get("/analysis/proximity", params=params).json()["results"]
    assert sum(r["covered_population"] for r in results) == covered_population


def test_types_are_analysed_separately(client):
    def contributing(params):
        [result] = client.get(
            "/analysis/proximity", params={"city": "Redlands", "radius_m": 1000, **params}
        ).json()["results"]
        return result["contributing_facilities"]

    assert contributing(SCHOOLS) + contributing(LIBRARIES) + contributing(TRANSIT) == contributing({})


@pytest.mark.parametrize("radius_m", [50, 3201, 5000, "abc"])
def test_invalid_radius_returns_422(client, radius_m):
    response = client.get("/analysis/proximity", params={"radius_m": radius_m})
    assert response.status_code == 422


def test_missing_radius_returns_422(client):
    assert client.get("/analysis/proximity").status_code == 422


def test_unknown_city_returns_404(client):
    response = client.get("/analysis/proximity", params={"city": "Atlantis", "radius_m": 500})
    assert response.status_code == 404
