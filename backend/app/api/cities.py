from typing import Annotated

from fastapi import APIRouter, Depends
from psycopg import Connection

from app.db import get_connection
from app.schemas.cities import CityCollection
from app.services import cities as cities_service

router = APIRouter(prefix="/cities", tags=["cities"])


@router.get("", response_model=CityCollection)
def list_cities(conn: Annotated[Connection, Depends(get_connection)]):
    """City boundaries (TIGER/Line 2026) as a GeoJSON FeatureCollection (EPSG:4326)."""
    return cities_service.list_cities(conn)
