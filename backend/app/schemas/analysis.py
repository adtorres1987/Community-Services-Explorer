from pydantic import BaseModel

from app.schemas.geojson import Geometry


class CityProximity(BaseModel):
    city: str
    eligible_facilities: int  # proximity-eligible facilities inside the place
    excluded_facilities: int  # inside the place but not eligible (exclusively virtual)
    contributing_facilities: int  # eligible facilities anywhere within the radius of the place
    # Their ids, so clients can count distinct facilities across several places
    contributing_facility_ids: list[int]
    city_area_km2: float
    covered_area_km2: float
    covered_pct: float
    population: int
    covered_population: int
    covered_population_pct: float
    coverage: Geometry | None  # area within the radius, clipped to the boundary


class ProximityResponse(BaseModel):
    radius_m: int
    facility_type: str | None
    facility_subtype: str | None
    method: str
    results: list[CityProximity]
