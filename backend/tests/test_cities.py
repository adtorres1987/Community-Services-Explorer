def test_list_cities(client):
    response = client.get("/cities")
    assert response.status_code == 200
    body = response.json()
    assert body["type"] == "FeatureCollection"

    cities = {f["properties"]["name"]: f for f in body["features"]}
    assert set(cities) == {"Redlands", "Yucaipa"}
    assert cities["Redlands"]["properties"]["facility_count"] == 24
    assert cities["Yucaipa"]["properties"]["facility_count"] == 13
    assert cities["Redlands"]["properties"]["area_km2"] == 93.86
    assert cities["Yucaipa"]["geometry"]["type"] == "MultiPolygon"
