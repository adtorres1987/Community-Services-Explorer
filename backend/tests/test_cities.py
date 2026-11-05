EXPECTED = {
    # name: (place_type, population 2020, facilities inside, area km²)
    "Colton": ("city", 53915, 15, 41.6),
    "Grand Terrace": ("city", 13148, 4, 9.07),
    "Highland": ("city", 56969, 10, 48.34),
    "Loma Linda": ("city", 24939, 2, 23.2),
    "Mentone": ("CDP", 9557, 2, 15.85),
    "Redlands": ("city", 73161, 22, 93.86),
    "Rialto": ("city", 104063, 28, 62.39),
    "San Bernardino": ("city", 222042, 77, 163.09),
    "Yucaipa": ("city", 54541, 13, 73.13),
}


def test_list_cities(client):
    response = client.get("/cities")
    assert response.status_code == 200
    body = response.json()
    assert body["type"] == "FeatureCollection"

    cities = {
        f["properties"]["name"]: (
            f["properties"]["place_type"],
            f["properties"]["population"],
            f["properties"]["facility_count"],
            f["properties"]["area_km2"],
        )
        for f in body["features"]
    }
    assert cities == EXPECTED
    assert {f["geometry"]["type"] for f in body["features"]} == {"MultiPolygon"}
