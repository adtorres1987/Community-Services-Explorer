from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from psycopg import Connection

from app.db import get_connection
from app.schemas.analysis import ProximityResponse
from app.services import analysis as analysis_service
from app.services import cities as cities_service

router = APIRouter(prefix="/analysis", tags=["analysis"])


@router.get("/proximity", response_model=ProximityResponse)
def proximity(
    conn: Annotated[Connection, Depends(get_connection)],
    radius_m: Annotated[int, Query(ge=100, le=2000, description="Radius in metres")],
    city: Annotated[str | None, Query(description="Omit for all cities")] = None,
    facility_type: Annotated[str | None, Query(description="e.g. school")] = None,
    facility_subtype: Annotated[str | None, Query(description="e.g. Elementary")] = None,
):
    """Share of each city's area within `radius_m` of a proximity-eligible facility."""
    if city is not None and not cities_service.city_exists(conn, city):
        raise HTTPException(status_code=404, detail=f"City '{city}' not found")
    return analysis_service.proximity(conn, city, radius_m, facility_type, facility_subtype)
