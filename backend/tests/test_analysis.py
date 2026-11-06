# Expected coverage values were verified independently with GeoPandas from
# data/processed/study_area.gpkg (see docs/database.md).
import pytest


@pytest.mark.parametrize(
    ("city", "radius_m", "area_pct", "population_pct", "contributing"),
    [
        ("Redlands", 500, 13.0, 24.2, 21),
        ("Redlands", 1000, 39.6, 74.8, 22),
        ("Yucaipa", 1000, 35.3, 59.4, 15),
        ("San Bernardino", 1000, 58.2, 88.3, 102),
        ("Mentone", 500, 10.5, 33.8, 3),
        ("Loma Linda", 1000, 25.9, 28.7, 5),
        ("Rialto", 1000, 65.7, 94.9, 43),
        ("Colton", 500, 20.1, 37.7, 18),
        ("Grand Terrace", 1000, 76.0, 90.4, 5),
    ],
)
def test_coverage_matches_verified_values(
    client, city, radius_m, area_pct, population_pct, contributing
):
    response = client.get("/analysis/proximity", params={"city": city, "radius_m": radius_m})
    assert response.status_code == 200
    [result] = response.json()["results"]
    assert result["city"] == city
    assert result["covered_pct"] == area_pct
    assert result["covered_population_pct"] == population_pct
    assert result["contributing_facilities"] == contributing
    assert result["coverage"]["type"] in {"Polygon", "MultiPolygon"}


def test_all_places_and_virtual_exclusion(client):
    body = client.get("/analysis/proximity", params={"radius_m": 500}).json()
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
        for r in client.get("/analysis/proximity", params={"radius_m": 1000}).json()["results"]
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
        "/analysis/proximity", params={"city": "Yucaipa", "radius_m": 1000}
    ).json()["results"]
    assert result["eligible_facilities"] == 13
    assert result["contributing_facilities"] == 15


def test_population_never_exceeds_total(client):
    body = client.get("/analysis/proximity", params={"radius_m": 2000}).json()
    for result in body["results"]:
        assert 0 <= result["covered_population"] <= result["population"]
        assert 0 <= result["covered_population_pct"] <= 100


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
    assert result["coverage"] is None


def test_filter_by_subtype(client):
    body = client.get(
        "/analysis/proximity",
        params={"city": "Redlands", "radius_m": 1000, "facility_subtype": "High"},
    ).json()
    [result] = body["results"]
    assert body["facility_subtype"] == "High"
    assert result["eligible_facilities"] == 3
    assert result["contributing_facilities"] == 4
    assert result["covered_population_pct"] == 15.9


@pytest.mark.parametrize("radius_m", [50, 5000, "abc"])
def test_invalid_radius_returns_422(client, radius_m):
    response = client.get("/analysis/proximity", params={"radius_m": radius_m})
    assert response.status_code == 422


def test_missing_radius_returns_422(client):
    assert client.get("/analysis/proximity").status_code == 422


def test_unknown_city_returns_404(client):
    response = client.get("/analysis/proximity", params={"city": "Atlantis", "radius_m": 500})
    assert response.status_code == 404
