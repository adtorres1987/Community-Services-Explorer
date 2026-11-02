# Integration tests: they run against the PostGIS container loaded with
# scripts/load_postgis.py (docker compose up -d --wait).
import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture(scope="session")
def client():
    with TestClient(app) as client:
        yield client
