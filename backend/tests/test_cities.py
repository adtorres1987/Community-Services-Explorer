EXPECTED = {
    # name: (place_type, population 2020, aged 5-17, facilities inside, area km²)
    "Colton": ("city", 53915, 10689, 15, 41.6),
    "Grand Terrace": ("city", 13148, 2129, 4, 9.07),
    "Highland": ("city", 56969, 11893, 10, 48.34),
    "Loma Linda": ("city", 24939, 3550, 2, 23.2),
    "Mentone": ("CDP", 9557, 1712, 2, 15.85),
    "Redlands": ("city", 73161, 12118, 22, 93.86),
    "Rialto": ("city", 104063, 21785, 28, 62.39),
    "San Bernardino": ("city", 222042, 46869, 77, 163.09),
    "Yucaipa": ("city", 54541, 9724, 13, 73.13),
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
            f["properties"]["population_5_17"],
            f["properties"]["facility_count"],
            f["properties"]["area_km2"],
        )
        for f in body["features"]
    }
    assert cities == EXPECTED
    assert {f["geometry"]["type"] for f in body["features"]} == {"MultiPolygon"}
