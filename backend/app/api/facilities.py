from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Path, Query
from psycopg import Connection

from app.db import get_connection
from app.schemas.facilities import FacilityCollection, FacilityFeature
from app.services import cities as cities_service
from app.services import facilities as facilities_service

router = APIRouter(prefix="/facilities", tags=["facilities"])


@router.get("", response_model=FacilityCollection)
def list_facilities(
    conn: Annotated[Connection, Depends(get_connection)],
    city: Annotated[str | None, Query(description="Address city, e.g. Redlands")] = None,
    facility_type: Annotated[str | None, Query(description="e.g. school")] = None,
    facility_subtype: Annotated[str | None, Query(description="e.g. Elementary")] = None,
):
    """Facilities as a GeoJSON FeatureCollection (EPSG:4326)."""
    if city is not None and not cities_service.city_exists(conn, city):
        raise HTTPException(status_code=404, detail=f"City '{city}' not found")
    return facilities_service.list_facilities(conn, city, facility_type, facility_subtype)


@router.get("/{facility_id}", response_model=FacilityFeature)
def get_facility(
    conn: Annotated[Connection, Depends(get_connection)],
    facility_id: Annotated[int, Path(ge=1)],
):
    """One facility as a GeoJSON Feature (EPSG:4326)."""
    facility = facilities_service.get_facility(conn, facility_id)
    if facility is None:
        raise HTTPException(status_code=404, detail=f"Facility {facility_id} not found")
    return facility
