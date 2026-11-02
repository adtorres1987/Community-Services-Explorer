from typing import Any, Literal

from pydantic import BaseModel

from app.schemas.geojson import Geometry


class FacilityProperties(BaseModel):
    id: int
    name: str
    facility_type: str
    facility_subtype: str | None
    city: str
    in_city_limits: bool
    proximity_eligible: bool
    attributes: dict[str, Any]


class FacilityFeature(BaseModel):
    type: Literal["Feature"] = "Feature"
    id: int
    geometry: Geometry
    properties: FacilityProperties


class FacilityCollection(BaseModel):
    type: Literal["FeatureCollection"] = "FeatureCollection"
    features: list[FacilityFeature]
