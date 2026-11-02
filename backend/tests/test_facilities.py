def test_list_all_facilities(client):
    response = client.get("/facilities")
    assert response.status_code == 200
    body = response.json()
    assert body["type"] == "FeatureCollection"
    assert len(body["features"]) == 37


def test_coordinates_are_wgs84_in_study_area(client):
    features = client.get("/facilities").json()["features"]
    for feature in features:
        lon, lat = feature["geometry"]["coordinates"]
        assert -117.3 < lon < -116.9
        assert 33.9 < lat < 34.2


def test_filter_by_city(client):
    features = client.get("/facilities", params={"city": "Yucaipa"}).json()["features"]
    assert len(features) == 13
    assert {f["properties"]["city"] for f in features} == {"Yucaipa"}


def test_filter_by_subtype(client):
    features = client.get(
        "/facilities", params={"city": "Redlands", "facility_subtype": "High"}
    ).json()["features"]
    assert len(features) == 4
    assert {f["properties"]["facility_subtype"] for f in features} == {"High"}


def test_unknown_city_returns_404(client):
    response = client.get("/facilities", params={"city": "Atlantis"})
    assert response.status_code == 404


def test_get_facility(client):
    first = client.get("/facilities").json()["features"][0]
    response = client.get(f"/facilities/{first['id']}")
    assert response.status_code == 200
    assert response.json() == first


def test_get_missing_facility_returns_404(client):
    assert client.get("/facilities/999999").status_code == 404


def test_invalid_facility_id_returns_422(client):
    assert client.get("/facilities/0").status_code == 422
    assert client.get("/facilities/abc").status_code == 422
