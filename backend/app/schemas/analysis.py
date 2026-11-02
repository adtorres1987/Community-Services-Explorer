from pydantic import BaseModel

from app.schemas.geojson import Geometry


class CityProximity(BaseModel):
    city: str
    city_area_km2: float
    eligible_facilities: int
    excluded_facilities: int  # not proximity eligible (exclusively virtual)
    covered_area_km2: float
    covered_pct: float
    coverage: Geometry | None  # city area within the radius, clipped to the boundary


class ProximityResponse(BaseModel):
    radius_m: int
    facility_type: str | None
    method: str
    results: list[CityProximity]
