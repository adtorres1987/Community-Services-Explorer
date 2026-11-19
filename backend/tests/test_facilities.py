def by_name(features, name):
    return next(f["properties"] for f in features if f["properties"]["name"] == name)


def test_list_all_facilities(client):
    response = client.get("/facilities")
    assert response.status_code == 200
    body = response.json()
    assert body["type"] == "FeatureCollection"
    assert len(body["features"]) == 1474
    assert sum(f["properties"]["in_study_area"] for f in body["features"]) == 1349


def test_list_facilities_by_type(client):
    for facility_type, total, in_study_area in (
        ("school", 205, 173), ("library", 20, 14), ("transit", 1249, 1162),
    ):
        features = client.get("/facilities", params={"facility_type": facility_type}).json()["features"]
        assert len(features) == total
        assert sum(f["properties"]["in_study_area"] for f in features) == in_study_area
        assert {f["properties"]["facility_type"] for f in features} == {facility_type}


def test_library_properties(client):
    features = client.get("/facilities", params={"facility_type": "library"}).json()["features"]
    smiley = by_name(features, "A. K. Smiley Public Library")
    assert (smiley["city"], smiley["facility_subtype"]) == ("Redlands", "Central")
    assert smiley["attributes"]["LibrarySystem"] == "A. K. Smiley Public Library"
    assert smiley["attributes"]["SquareFeet"] == 64636
    calimesa = by_name(features, "Calimesa Library")
    assert (calimesa["city"], calimesa["in_study_area"]) == (None, False)


def test_transit_stop_properties(client):
    features = client.get(
        "/facilities", params={"facility_type": "transit", "facility_subtype": "Rail"}
    ).json()["features"]
    assert len(features) == 7
    downtown = by_name(features, "San Bernardino - Downtown")
    assert downtown["city"] == "San Bernardino"
    assert downtown["address_city"] is None
    assert downtown["attributes"]["Routes"] == "IE-OC Line, SB Line"
    assert downtown["attributes"]["PeakDeparturesPerHour"] == 5.0


def test_context_facilities_have_no_study_city(client):
    for feature in client.get("/facilities").json()["features"]:
        properties = feature["properties"]
        assert properties["in_study_area"] == (properties["city"] is not None)


def test_coordinates_are_wgs84_near_study_area(client):
    features = client.get("/facilities").json()["features"]
    for feature in features:
        lon, lat = feature["geometry"]["coordinates"]
        assert -117.50 < lon < -116.95
        assert 33.95 < lat < 34.30


def test_city_is_assigned_by_boundary_not_address(client):
    features = client.get("/facilities").json()["features"]
    mission = by_name(features, "Mission Elementary")
    assert (mission["city"], mission["address_city"]) == ("Loma Linda", "Redlands")
    rev = by_name(features, "Redlands East Valley High")
    assert (rev["city"], rev["address_city"]) == ("Mentone", "Redlands")


def test_filter_by_city(client):
    features = client.get("/facilities", params={"city": "Yucaipa"}).json()["features"]
    assert len(features) == 74
    assert {f["properties"]["city"] for f in features} == {"Yucaipa"}
    types = [f["properties"]["facility_type"] for f in features]
    assert (types.count("school"), types.count("library"), types.count("transit")) == (13, 1, 60)


def test_filter_by_subtype(client):
    features = client.get(
        "/facilities", params={"city": "Redlands", "facility_subtype": "High"}
    ).json()["features"]
    assert len(features) == 3
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
