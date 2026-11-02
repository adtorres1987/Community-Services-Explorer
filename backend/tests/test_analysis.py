# Expected coverage values were verified independently with GeoPandas
# (see docs/database.md).
import pytest


@pytest.mark.parametrize(
    ("city", "radius_m", "expected_pct"),
    [
        ("Redlands", 500, 12.9),
        ("Redlands", 1000, 38.8),
        ("Yucaipa", 500, 11.1),
        ("Yucaipa", 1000, 34.7),
    ],
)
def test_coverage_matches_verified_values(client, city, radius_m, expected_pct):
    response = client.get("/analysis/proximity", params={"city": city, "radius_m": radius_m})
    assert response.status_code == 200
    [result] = response.json()["results"]
    assert result["city"] == city
    assert result["covered_pct"] == expected_pct
    assert result["coverage"]["type"] in {"Polygon", "MultiPolygon"}


def test_all_cities_and_virtual_exclusion(client):
    body = client.get("/analysis/proximity", params={"radius_m": 500}).json()
    results = {r["city"]: r for r in body["results"]}
    assert set(results) == {"Redlands", "Yucaipa"}
    # Four exclusively virtual schools in Redlands are not proximity eligible
    assert results["Redlands"]["eligible_facilities"] == 20
    assert results["Redlands"]["excluded_facilities"] == 4
    assert results["Yucaipa"]["eligible_facilities"] == 13
    assert "Straight-line" in body["method"]


def test_type_without_facilities_has_no_coverage(client):
    body = client.get(
        "/analysis/proximity", params={"city": "Yucaipa", "radius_m": 500, "facility_type": "park"}
    ).json()
    [result] = body["results"]
    assert result["eligible_facilities"] == 0
    assert result["covered_pct"] == 0
    assert result["coverage"] is None


def test_filter_by_subtype(client):
    body = client.get(
        "/analysis/proximity",
        params={"city": "Redlands", "radius_m": 1000, "facility_subtype": "High"},
    ).json()
    [result] = body["results"]
    assert body["facility_subtype"] == "High"
    assert result["eligible_facilities"] == 4
    all_types = client.get(
        "/analysis/proximity", params={"city": "Redlands", "radius_m": 1000}
    ).json()["results"][0]
    assert 0 < result["covered_pct"] < all_types["covered_pct"]


@pytest.mark.parametrize("radius_m", [50, 5000, "abc"])
def test_invalid_radius_returns_422(client, radius_m):
    response = client.get("/analysis/proximity", params={"radius_m": radius_m})
    assert response.status_code == 422


def test_missing_radius_returns_422(client):
    assert client.get("/analysis/proximity").status_code == 422


def test_unknown_city_returns_404(client):
    response = client.get("/analysis/proximity", params={"city": "Atlantis", "radius_m": 500})
    assert response.status_code == 404
