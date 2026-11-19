EXPECTED = {
    # name: (place_type, population 2020, aged 5-17, schools, libraries, transit stops, area km²)
    "Colton": ("city", 53915, 10689, 15, 2, 93, 41.6),
    "Grand Terrace": ("city", 13148, 2129, 4, 1, 13, 9.07),
    "Highland": ("city", 56969, 11893, 10, 1, 71, 48.34),
    "Loma Linda": ("city", 24939, 3550, 2, 1, 55, 23.2),
    "Mentone": ("CDP", 9557, 1712, 2, 1, 20, 15.85),
    "Redlands": ("city", 73161, 12118, 22, 1, 99, 93.86),
    "Rialto": ("city", 104063, 21785, 28, 2, 197, 62.39),
    "San Bernardino": ("city", 222042, 46869, 77, 4, 554, 163.09),
    "Yucaipa": ("city", 54541, 9724, 13, 1, 60, 73.13),
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
            f["properties"]["facility_counts"]["school"],
            f["properties"]["facility_counts"]["library"],
            f["properties"]["facility_counts"]["transit"],
            f["properties"]["area_km2"],
        )
        for f in body["features"]
    }
    assert cities == EXPECTED
    for f in body["features"]:
        properties = f["properties"]
        assert properties["facility_count"] == sum(properties["facility_counts"].values())
    assert {f["geometry"]["type"] for f in body["features"]} == {"MultiPolygon"}
